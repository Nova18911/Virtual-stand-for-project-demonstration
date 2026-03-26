import docker
import pg8000
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import schedule
import signal
import sys
from dataclasses import dataclass
import os

@dataclass
class ContainerInfo:
    """Класс для хранения информации о контейнере"""
    container_id: str
    project_id: int
    port: int
    image_name: str
    started_at: datetime
    status: str

class DockerLifecycleManager:
    def __init__(self):
        """Инициализация менеджера"""
        self.client = None
        self.docker_available = False
        self._init_docker_client()
        
        self.logger = self._setup_logging()
        self.running = True
        
        # Подключение к PostgreSQL
        try:
            self.db_conn = pg8000.connect(
                host="127.0.0.1",
                port=5432,
                database="course_management",
                user="postgres",
                password="endermen"
            )
            self.logger.info("Подключение к PostgreSQL успешно")
        except Exception as e:
            self.logger.error(f"Ошибка подключения к PostgreSQL: {e}")
            raise
        
        self._setup_signal_handlers()
        self._init_database()
        
    def _init_docker_client(self):
        """Инициализация Docker клиента с обработкой ошибок"""
        try:
            # Проверяем, запущен ли Docker
            self.client = docker.from_env()
            # Проверяем версию Docker
            version = self.client.version()
            self.docker_available = True
            print(f"Docker доступен, версия: {version.get('Version', 'unknown')}")
        except Exception as e:
            self.docker_available = False
            print(f"Предупреждение: Docker не доступен - {e}")
            print("Функции управления контейнерами будут отключены")
            print("Для работы с Docker убедитесь, что Docker Desktop запущен")
    
    def _setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('docker_lifecycle.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def _setup_signal_handlers(self):
        """Настройка обработчиков сигналов"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов завершения"""
        self.logger.info("Получен сигнал завершения. Останавливаем менеджер...")
        self.running = False
        if hasattr(self, 'db_conn') and self.db_conn:
            self.db_conn.close()
    
    def _init_database(self):
        """Инициализация таблиц в PostgreSQL"""
        try:
            cursor = self.db_conn.cursor()
            
            # Создание таблицы docker_containers
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS docker_containers (
                    container_id VARCHAR(64) PRIMARY KEY,
                    project_id INTEGER NOT NULL,
                    port INTEGER NOT NULL,
                    image_name VARCHAR(255) NOT NULL,
                    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'running'
                )
            """)
            
            # Создание таблицы для истории удалений
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cleanup_history (
                    id SERIAL PRIMARY KEY,
                    container_id VARCHAR(64),
                    image_name VARCHAR(255),
                    project_id INTEGER,
                    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reason VARCHAR(100)
                )
            """)
            
            # Создание таблицы настроек
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cleanup_settings (
                    id SERIAL PRIMARY KEY,
                    container_lifetime_hours INTEGER DEFAULT 24,
                    image_cleanup_enabled BOOLEAN DEFAULT TRUE,
                    check_interval_minutes INTEGER DEFAULT 5,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Вставка настроек по умолчанию
            cursor.execute("SELECT COUNT(*) FROM cleanup_settings")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO cleanup_settings 
                    (container_lifetime_hours, image_cleanup_enabled, check_interval_minutes)
                    VALUES (24, TRUE, 5)
                """)
            
            self.db_conn.commit()
            self.logger.info("База данных PostgreSQL инициализирована")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации базы данных: {e}")
            raise
    
    def register_container(self, container_id: str, project_id: int, 
                          port: int, image_name: str) -> bool:
        """Регистрация контейнера в базе данных"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO docker_containers 
                (container_id, project_id, port, image_name, started_at, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                container_id, 
                project_id, 
                port, 
                image_name, 
                datetime.now(),
                'running'
            ))
            self.db_conn.commit()
            self.logger.info(f"Контейнер {container_id} зарегистрирован")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка регистрации контейнера: {e}")
            return False
    
    def get_expired_containers(self, lifetime_hours: int = 24) -> List[ContainerInfo]:
        """Получение списка контейнеров, которые нужно удалить"""
        try:
            expiration_time = datetime.now() - timedelta(hours=lifetime_hours)
            
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT container_id, project_id, port, image_name, started_at, status
                FROM docker_containers
                WHERE status = 'running' 
                AND started_at < %s
            """, (expiration_time,))
            
            containers = []
            for row in cursor.fetchall():
                containers.append(ContainerInfo(
                    container_id=row[0],
                    project_id=row[1],
                    port=row[2],
                    image_name=row[3],
                    started_at=row[4],
                    status=row[5]
                ))
            
            return containers
        except Exception as e:
            self.logger.error(f"Ошибка получения просроченных контейнеров: {e}")
            return []
    
    def stop_and_remove_container(self, container_info: ContainerInfo) -> bool:
        """Остановка и удаление контейнера"""
        if not self.docker_available:
            self.logger.warning("Docker недоступен, пропускаем удаление контейнера")
            return False
            
        try:
            container = self.client.containers.get(container_info.container_id)
            
            # Остановка контейнера
            self.logger.info(f"Останавливаем контейнер {container_info.container_id}")
            container.stop(timeout=10)
            
            # Удаление контейнера
            self.logger.info(f"Удаляем контейнер {container_info.container_id}")
            container.remove()
            
            # Обновление статуса в БД
            cursor = self.db_conn.cursor()
            cursor.execute("""
                UPDATE docker_containers 
                SET status = 'removed' 
                WHERE container_id = %s
            """, (container_info.container_id,))
            
            # Запись в историю
            cursor.execute("""
                INSERT INTO cleanup_history 
                (container_id, image_name, project_id, reason)
                VALUES (%s, %s, %s, %s)
            """, (
                container_info.container_id,
                container_info.image_name,
                container_info.project_id,
                'timeout_expired'
            ))
            self.db_conn.commit()
            
            self.logger.info(f"Контейнер {container_info.container_id} успешно удален")
            return True
            
        except docker.errors.NotFound:
            self.logger.warning(f"Контейнер {container_info.container_id} не найден")
            cursor = self.db_conn.cursor()
            cursor.execute("""
                UPDATE docker_containers 
                SET status = 'not_found' 
                WHERE container_id = %s
            """, (container_info.container_id,))
            self.db_conn.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка удаления контейнера {container_info.container_id}: {e}")
            return False
    
    def cleanup_unused_images(self, days_old: int = 7) -> Dict[str, int]:
        """Очистка неиспользуемых образов"""
        if not self.docker_available:
            self.logger.warning("Docker недоступен, пропускаем очистку образов")
            return {'images_removed': 0, 'space_freed': 0}
            
        try:
            stats = {
                'images_removed': 0,
                'space_freed': 0
            }
            
            images = self.client.images.list()
            
            # Получаем список используемых образов
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT DISTINCT image_name 
                FROM docker_containers 
                WHERE status = 'running'
            """)
            used_images = set(row[0] for row in cursor.fetchall())
            
            # Текущее время
            now = datetime.now()
            
            for image in images:
                tags = image.tags
                if not tags:
                    continue
                
                # Проверяем, используется ли образ
                in_use = any(tag in used_images for tag in tags)
                
                if not in_use:
                    # Проверяем возраст образа
                    try:
                        created_timestamp = image.attrs['Created']
                        
                        # Преобразуем в datetime
                        if isinstance(created_timestamp, str):
                            # Убираем часовой пояс
                            if 'Z' in created_timestamp:
                                created_timestamp = created_timestamp.replace('Z', '')
                            if 'T' in created_timestamp:
                                # Парсим ISO формат
                                date_part, time_part = created_timestamp.split('T')
                                time_part = time_part.split('.')[0][:8]  # Берем только HH:MM:SS
                                created = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S")
                            else:
                                created = datetime.strptime(created_timestamp, "%Y-%m-%d %H:%M:%S")
                        else:
                            created = datetime.fromtimestamp(created_timestamp)
                        
                        # Вычисляем возраст
                        age_days = (now - created).days
                        
                        if age_days > days_old:
                            try:
                                size = image.attrs['Size']
                                self.client.images.remove(image.id, force=True)
                                stats['images_removed'] += 1
                                stats['space_freed'] += size
                                self.logger.info(f"Удален образ {tags} (возраст: {age_days} дней)")
                            except Exception as e:
                                self.logger.error(f"Ошибка удаления образа {tags}: {e}")
                        
                    except Exception as e:
                        self.logger.error(f"Ошибка обработки образа {tags}: {e}")
                        continue
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки образов: {e}")
            return {'images_removed': 0, 'space_freed': 0}
    
    def get_container_stats(self) -> Dict:
        """Получение статистики по контейнерам"""
        try:
            cursor = self.db_conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
                    SUM(CASE WHEN status = 'removed' THEN 1 ELSE 0 END) as removed,
                    SUM(CASE WHEN status = 'not_found' THEN 1 ELSE 0 END) as not_found
                FROM docker_containers
            """)
            stats = cursor.fetchone()
            
            cursor.execute("""
                SELECT 
                    project_id,
                    COUNT(*) as count,
                    MAX(started_at) as last_started
                FROM docker_containers
                WHERE status = 'running'
                GROUP BY project_id
            """)
            projects_stats = cursor.fetchall()
            
            return {
                'total': stats[0] if stats else 0,
                'running': stats[1] if stats else 0,
                'removed': stats[2] if stats else 0,
                'not_found': stats[3] if stats else 0,
                'docker_available': self.docker_available,
                'projects': [{'project_id': p[0], 'count': p[1], 'last_started': p[2].isoformat() if p[2] else None} for p in projects_stats]
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    def manual_cleanup(self, container_id: Optional[str] = None, 
                      project_id: Optional[int] = None) -> bool:
        """Ручная очистка контейнеров"""
        if not self.docker_available:
            self.logger.warning("Docker недоступен, ручная очистка невозможна")
            return False
            
        try:
            if container_id:
                cursor = self.db_conn.cursor()
                cursor.execute("""
                    SELECT container_id, project_id, port, image_name, started_at, status
                    FROM docker_containers
                    WHERE container_id = %s AND status = 'running'
                """, (container_id,))
                row = cursor.fetchone()
                
                if row:
                    container_info = ContainerInfo(
                        container_id=row[0],
                        project_id=row[1],
                        port=row[2],
                        image_name=row[3],
                        started_at=row[4],
                        status=row[5]
                    )
                    return self.stop_and_remove_container(container_info)
                    
            elif project_id:
                cursor = self.db_conn.cursor()
                cursor.execute("""
                    SELECT container_id, project_id, port, image_name, started_at, status
                    FROM docker_containers
                    WHERE project_id = %s AND status = 'running'
                """, (project_id,))
                rows = cursor.fetchall()
                
                success = True
                for row in rows:
                    container_info = ContainerInfo(
                        container_id=row[0],
                        project_id=row[1],
                        port=row[2],
                        image_name=row[3],
                        started_at=row[4],
                        status=row[5]
                    )
                    if not self.stop_and_remove_container(container_info):
                        success = False
                return success
                
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка ручной очистки: {e}")
            return False
    
    def run_cleanup_cycle(self):
        """Выполнение цикла очистки"""
        self.logger.info("Запуск цикла очистки...")
        
        # Получаем настройки
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT container_lifetime_hours, image_cleanup_enabled
            FROM cleanup_settings
            ORDER BY id DESC LIMIT 1
        """)
        settings = cursor.fetchone()
        lifetime_hours = settings[0] if settings else 24
        image_cleanup_enabled = settings[1] if settings else True
        
        # Удаляем просроченные контейнеры
        expired_containers = self.get_expired_containers(lifetime_hours)
        removed_count = 0
        
        for container in expired_containers:
            if self.stop_and_remove_container(container):
                removed_count += 1
        
        self.logger.info(f"Удалено просроченных контейнеров: {removed_count}")
        
        # Очищаем неиспользуемые образы
        if image_cleanup_enabled:
            cleanup_stats = self.cleanup_unused_images()
            if cleanup_stats['images_removed'] > 0:
                self.logger.info(
                    f"Удалено образов: {cleanup_stats['images_removed']}, "
                    f"освобождено места: {cleanup_stats['space_freed'] / 1024 / 1024:.2f} MB"
                )
    
    def start_scheduler(self):
        """Запуск планировщика задач"""
        self.logger.info("Запуск планировщика...")
        
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT check_interval_minutes
            FROM cleanup_settings
            ORDER BY id DESC LIMIT 1
        """)
        result = cursor.fetchone()
        interval = result[0] if result else 5
        
        schedule.every(interval).minutes.do(self.run_cleanup_cycle)
        self.run_cleanup_cycle()
        
        while self.running:
            schedule.run_pending()
            time.sleep(1)
        
        self.logger.info("Планировщик остановлен")
    
    def update_settings(self, container_lifetime_hours: int = 24,
                       image_cleanup_enabled: bool = True,
                       check_interval_minutes: int = 5) -> bool:
        """Обновление настроек очистки"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO cleanup_settings 
                (container_lifetime_hours, image_cleanup_enabled, check_interval_minutes, updated_at)
                VALUES (%s, %s, %s, %s)
            """, (container_lifetime_hours, image_cleanup_enabled, check_interval_minutes, datetime.now()))
            self.db_conn.commit()
            
            self.logger.info(f"Настройки обновлены: время жизни={container_lifetime_hours}ч, "
                           f"очистка образов={image_cleanup_enabled}, интервал={check_interval_minutes}мин")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления настроек: {e}")
            return False