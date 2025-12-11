-- Create MSSQL test database for construction management system
-- Run this script as a user with CREATE DATABASE permissions (e.g., sa or q1 with appropriate rights)

-- Create database if it doesn't exist
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'construction')
BEGIN
    CREATE DATABASE construction;
    PRINT 'Database "construction" created successfully';
END
ELSE
BEGIN
    PRINT 'Database "construction" already exists';
END
GO

-- Switch to the construction database
USE construction;
GO

-- Grant permissions to user q1 (if needed)
-- Uncomment if you need to grant permissions
-- IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'q1')
-- BEGIN
--     CREATE USER q1 FOR LOGIN q1;
-- END
-- GO
-- 
-- ALTER ROLE db_owner ADD MEMBER q1;
-- GO

PRINT 'Database setup complete';
PRINT 'You can now run the MSSQL tests';
