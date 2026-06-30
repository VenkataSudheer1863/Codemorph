-- =====================================================================
-- University Academic Management System — Database Schema
-- Compatible with PostgreSQL 12+
-- =====================================================================

-- Drop tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS results CASCADE;
DROP TABLE IF EXISTS exams CASCADE;
DROP TABLE IF EXISTS enrollments CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS faculty CASCADE;
DROP TABLE IF EXISTS students CASCADE;

-- =====================================================================
-- TABLE: students
-- =====================================================================
CREATE TABLE students (
    student_id      BIGSERIAL PRIMARY KEY,
    first_name      VARCHAR(100)  NOT NULL,
    last_name       VARCHAR(100)  NOT NULL,
    email           VARCHAR(200)  NOT NULL UNIQUE,
    department      VARCHAR(100)  NOT NULL,
    year_of_study   INTEGER       NOT NULL CHECK (year_of_study BETWEEN 1 AND 6),
    password_hash   VARCHAR(500)  NOT NULL,
    created_at      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_students_email      ON students(email);
CREATE INDEX idx_students_department ON students(department);

-- =====================================================================
-- TABLE: faculty
-- =====================================================================
CREATE TABLE faculty (
    faculty_id    BIGSERIAL PRIMARY KEY,
    name          VARCHAR(200)  NOT NULL,
    email         VARCHAR(200)  NOT NULL UNIQUE,
    department    VARCHAR(100)  NOT NULL,
    designation   VARCHAR(100)  NOT NULL,
    password_hash VARCHAR(500)  NOT NULL,
    created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_faculty_email      ON faculty(email);
CREATE INDEX idx_faculty_department ON faculty(department);

-- =====================================================================
-- TABLE: courses
-- =====================================================================
CREATE TABLE courses (
    course_id     BIGSERIAL PRIMARY KEY,
    course_name   VARCHAR(200)  NOT NULL,
    credits       INTEGER       NOT NULL CHECK (credits BETWEEN 1 AND 10),
    department    VARCHAR(100)  NOT NULL,
    faculty_id    BIGINT        REFERENCES faculty(faculty_id) ON DELETE SET NULL,
    created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_courses_faculty_id  ON courses(faculty_id);
CREATE INDEX idx_courses_department  ON courses(department);

-- =====================================================================
-- TABLE: enrollments
-- =====================================================================
CREATE TABLE enrollments (
    enrollment_id BIGSERIAL PRIMARY KEY,
    student_id    BIGINT       NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    course_id     BIGINT       NOT NULL REFERENCES courses(course_id)   ON DELETE CASCADE,
    semester      VARCHAR(20)  NOT NULL,
    enrolled_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_enrollment UNIQUE (student_id, course_id, semester)
);

CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_course  ON enrollments(course_id);

-- =====================================================================
-- TABLE: exams
-- =====================================================================
CREATE TABLE exams (
    exam_id          BIGSERIAL PRIMARY KEY,
    course_id        BIGINT       NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    exam_date        DATE         NOT NULL,
    exam_type        VARCHAR(50),
    location         VARCHAR(200),
    duration_minutes INTEGER,
    created_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_exams_course_id ON exams(course_id);
CREATE INDEX idx_exams_date      ON exams(exam_date);

-- =====================================================================
-- TABLE: results
-- =====================================================================
CREATE TABLE results (
    result_id      BIGSERIAL PRIMARY KEY,
    student_id     BIGINT       NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    course_id      BIGINT       NOT NULL REFERENCES courses(course_id)   ON DELETE CASCADE,
    grade          VARCHAR(5)   NOT NULL,
    marks_obtained DECIMAL(6,2),
    total_marks    DECIMAL(6,2),
    remarks        VARCHAR(500),
    published_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_result UNIQUE (student_id, course_id)
);

CREATE INDEX idx_results_student ON results(student_id);
CREATE INDEX idx_results_course  ON results(course_id);

-- =====================================================================
-- SAMPLE SEED DATA
-- Admin password: Admin@123 (SHA-256 hash)
-- Test password for all: Test@123 (SHA-256 hash)
-- SHA-256("Admin@123") = 5cAtyCDHIjr3CnlJYq1PCDO7bh7P1wKm9WmGOJsw9FY= (Base64)
-- SHA-256("Test@123")  = 5cAtyCDHIjr3CnlJYq1PCDO7bh7P1wKm9WmGOJsw9FY= (use actual hash)
-- =====================================================================

-- Sample Faculty
INSERT INTO faculty (name, email, department, designation, password_hash)
VALUES
    ('Dr. Alan Watson',       'alan.watson@university.edu',   'Computer Science',      'Professor',           'f7+8wePKS5w1tVW2gxJFUaWFV6Cly33rjZvLYBPCxaQ='),
    ('Prof. Susan Patel',     'susan.patel@university.edu',   'Mathematics',           'Associate Professor', 'f7+8wePKS5w1tVW2gxJFUaWFV6Cly33rjZvLYBPCxaQ='),
    ('Dr. Michael Chen',      'michael.chen@university.edu',  'Electronics Engineering','Assistant Professor', 'f7+8wePKS5w1tVW2gxJFUaWFV6Cly33rjZvLYBPCxaQ='),
    ('Dr. Priya Sharma',      'priya.sharma@university.edu',  'Information Technology', 'Professor',           'f7+8wePKS5w1tVW2gxJFUaWFV6Cly33rjZvLYBPCxaQ=');

-- Sample Courses
INSERT INTO courses (course_name, credits, department, faculty_id)
VALUES
    ('Data Structures and Algorithms', 4, 'Computer Science',      1),
    ('Operating Systems',              3, 'Computer Science',      1),
    ('Calculus and Linear Algebra',    4, 'Mathematics',           2),
    ('Digital Electronics',            3, 'Electronics Engineering',3),
    ('Database Management Systems',    3, 'Information Technology', 4),
    ('Web Technologies',               3, 'Information Technology', 4);

-- Sample Students
INSERT INTO students (first_name, last_name, email, department, year_of_study, password_hash)
VALUES
    ('Alice',   'Johnson',   'alice.johnson@student.edu',   'Computer Science',      2, 'f7+8wePKS5w1tVW2gxJFUaWFV6Cly33rjZvLYBPCxaQ='),
    ('Bob',     'Williams',  'bob.williams@student.edu',    'Information Technology', 3, 'f7+8wePKS5w1tVW2gxJFUaWFV6Cly33rjZvLYBPCxaQ='),
    ('Carol',   'Davis',     'carol.davis@student.edu',     'Mathematics',            1, 'f7+8wePKS5w1tVW2gxJFUaWFV6Cly33rjZvLYBPCxaQ='),
    ('Daniel',  'Martinez',  'daniel.martinez@student.edu', 'Computer Science',      2, 'f7+8wePKS5w1tVW2gxJFUaWFV6Cly33rjZvLYBPCxaQ=');

-- Sample Enrollments
INSERT INTO enrollments (student_id, course_id, semester)
VALUES
    (1, 1, 'Fall 2025'),
    (1, 5, 'Fall 2025'),
    (2, 5, 'Fall 2025'),
    (2, 6, 'Fall 2025'),
    (3, 3, 'Fall 2025'),
    (4, 1, 'Fall 2025'),
    (4, 2, 'Fall 2025');

-- Sample Exams
INSERT INTO exams (course_id, exam_date, exam_type, location, duration_minutes)
VALUES
    (1, '2026-04-15', 'Midterm', 'Hall A', 120),
    (2, '2026-04-20', 'Midterm', 'Hall B', 90),
    (5, '2026-04-22', 'Midterm', 'Lab 1',  60);

-- Sample Results
INSERT INTO results (student_id, course_id, grade, marks_obtained, total_marks, remarks)
VALUES
    (1, 1, 'A+', 95.0, 100.0, 'Excellent performance'),
    (2, 5, 'B+', 78.0, 100.0, 'Good understanding'),
    (3, 3, 'A',  88.0, 100.0, 'Very good'),
    (4, 1, 'B',  72.0, 100.0, 'Above average');
