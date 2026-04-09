# cleanup_docker.py
import docker


def clean_all_student_resources():
    client = docker.from_env()

    print("=" * 50)
    print("🧹 Начинаем полную очистку Docker ресурсов")
    print("=" * 50)

    # 1. Останавливаем и удаляем все контейнеры
    print("\n1. Останавливаем и удаляем контейнеры...")
    containers = client.containers.list(all=True)
    removed_containers = 0

    for container in containers:
        try:
            # Просто удаляем все контейнеры, не проверяя их имена
            print(f"   Удаляем контейнер: {container.id[:12]}")
            container.stop(timeout=5)
            container.remove()
            removed_containers += 1
            print(f"   ✅ Контейнер удален")
        except Exception as e:
            print(f"   ⚠️ Ошибка: {e}")

    print(f"   Удалено контейнеров: {removed_containers}")

    # 2. Удаляем все образы с student_ в названии
    print("\n2. Удаляем образы...")
    images = client.images.list()
    removed_images = 0

    for image in images:
        try:
            for tag in image.tags:
                if 'student_' in tag:
                    print(f"   Удаляем образ: {tag}")
                    client.images.remove(image.id, force=True)
                    removed_images += 1
                    print(f"   ✅ Образ удален")
                    break
        except Exception as e:
            print(f"   ⚠️ Ошибка при удалении образа: {e}")

    print(f"   Удалено образов: {removed_images}")

    # 3. Очищаем неиспользуемые ресурсы
    print("\n3. Очищаем неиспользуемые ресурсы...")
    try:
        client.containers.prune()
        client.images.prune()
        client.volumes.prune()
        client.networks.prune()
        print("   ✅ Очистка завершена")
    except Exception as e:
        print(f"   ⚠️ Ошибка: {e}")

    print("\n" + "=" * 50)
    print("✅ Очистка Docker ресурсов завершена!")
    print("=" * 50)

    # 4. Показываем остатки
    print("\n4. Оставшиеся контейнеры:")
    remaining = client.containers.list(all=True)
    if remaining:
        for c in remaining:
            print(f"   - {c.id[:12]}: {c.name} ({c.status})")
    else:
        print("   Нет контейнеров")

    print("\n5. Оставшиеся образы с 'student_':")
    remaining_images = [img for img in client.images.list()
                        if any('student_' in tag for tag in img.tags)]
    if remaining_images:
        for img in remaining_images:
            print(f"   - {img.tags}")
    else:
        print("   Нет образов с 'student_'")


def clean_specific_image(image_name="student_4_lab_3"):
    """Удаляет конкретный образ"""
    try:
        client = docker.from_env()
        print(f"Удаляем образ {image_name}...")

        # Сначала останавливаем все контейнеры с этим образом
        containers = client.containers.list(all=True)
        for container in containers:
            try:
                if container.image.tags and image_name in container.image.tags[0]:
                    print(f"  Останавливаем контейнер {container.id[:12]}")
                    container.stop(timeout=5)
                    container.remove()
            except:
                pass

        # Удаляем образ
        client.images.remove(image_name, force=True)
        print(f"✅ Образ {image_name} удален")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    # Удаляем конкретный проблемный образ
    clean_specific_image("student_4_lab_3")

    # Полная очистка
    clean_all_student_resources()