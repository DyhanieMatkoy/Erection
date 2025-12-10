-- Тестовые пользователи (пароли: admin, manager, foreman)
INSERT INTO users (username, password_hash, role, is_active) VALUES
('admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'Администратор', 1),
('manager', '6ee4a469cd4e91053847f5d3fcb61dbcc91e8f0ef10be7748da4c4a1ba382d17', 'Руководитель', 1),
('foreman', 'c6de3c105315372cbbc427cb3a96544cb9edc0f91b557deccfe10442fad08854', 'Бригадир', 1);

-- Физлица
INSERT INTO persons (full_name, position, phone, user_id) VALUES
('Иванов Иван Иванович', 'Администратор', '+7-900-123-45-67', 1),
('Петров Петр Петрович', 'Руководитель проекта', '+7-900-234-56-78', 2),
('Сидоров Сидор Сидорович', 'Бригадир', '+7-900-345-67-89', 3);

-- Организации
INSERT INTO organizations (name, inn, default_responsible_id) VALUES
('ООО "СтройМастер"', '7701234567', 2);

-- Контрагенты
INSERT INTO counterparties (name, inn, contact_person, phone) VALUES
('ООО "Заказчик-1"', '7702345678', 'Смирнов А.А.', '+7-900-456-78-90'),
('ООО "Заказчик-2"', '7703456789', 'Кузнецов Б.Б.', '+7-900-567-89-01');

-- Объекты
INSERT INTO objects (name, owner_id, address) VALUES
('Жилой комплекс "Солнечный"', 1, 'г. Москва, ул. Солнечная, д. 1'),
('Торговый центр "Центральный"', 2, 'г. Москва, пр. Центральный, д. 10');

-- Работы
INSERT INTO works (name, unit, price, labor_rate) VALUES
('Кладка кирпича', 'м³', 5000.00, 8.0),
('Штукатурка стен', 'м²', 500.00, 0.5),
('Покраска стен', 'м²', 300.00, 0.3),
('Монтаж окон', 'шт', 3000.00, 2.0),
('Укладка плитки', 'м²', 800.00, 1.0);

-- Константы
INSERT INTO constants (key, value) VALUES
('ОсновнаяОрганизация', '1'),
('ОсновнойОтветственный', '2');
