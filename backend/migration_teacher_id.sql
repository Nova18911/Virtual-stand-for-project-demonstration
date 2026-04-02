-- Добавляем teacher_id в таблицу courses
ALTER TABLE courses ADD COLUMN IF NOT EXISTS teacher_id INTEGER;

-- Добавляем внешний ключ
ALTER TABLE courses
    ADD CONSTRAINT fk_courses_teacher
    FOREIGN KEY (teacher_id) REFERENCES users(user_id)
    ON UPDATE CASCADE ON DELETE SET NULL;

-- Заполняем teacher_id для уже существующих курсов по имени преподавателя
UPDATE courses c
SET teacher_id = u.user_id
FROM users u
JOIN passwords p ON u.login_id = p.login_id
JOIN roles r ON u.access_id = r.access_id
WHERE r.access_rights = 'teacher'
  AND u.full_name = c.teacher
  AND c.teacher_id IS NULL;
