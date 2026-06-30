# University Academic Management System (UniAMS)
## A Complete Java EE Enterprise Application

---

## 🏢 Project Overview

**UniAMS** is a complete enterprise-grade University Academic Management System built with the full Java EE technology stack:

| Layer | Technology |
|-------|-----------|
| Presentation | **JSF 2.3** (JavaServer Faces) |
| Business | **EJB 3.2** (Stateless Session Beans) |
| REST Services | **JAX-RS** (RESTful APIs) |
| SOAP Services | **JAX-WS** (Web Services) |
| Persistence | **JPA 2.2** (Java Persistence API + Hibernate) |
| Database | **PostgreSQL 12+** |
| Server | **WildFly 26.x** |
| Build | **Maven 3.8+** |

---

## 📁 Project Structure

```
university-system/
├── pom.xml                          ← Root Maven POM (multi-module)
│
├── university-persistence/          ← JPA Entities + Repositories
│   └── src/main/java/
│       └── com/university/persistence/
│           ├── entity/
│           │   ├── Student.java
│           │   ├── Faculty.java
│           │   ├── Course.java
│           │   ├── Enrollment.java
│           │   ├── Exam.java
│           │   └── Result.java
│           └── repository/
│               ├── StudentRepository.java
│               ├── FacultyRepository.java
│               ├── CourseRepository.java
│               ├── EnrollmentRepository.java
│               ├── ExamRepository.java
│               └── ResultRepository.java
│
├── university-ejb/                  ← EJB Business Logic
│   └── src/main/java/
│       └── com/university/ejb/service/
│           ├── StudentServiceBean.java
│           ├── FacultyServiceBean.java
│           ├── CourseServiceBean.java
│           ├── EnrollmentServiceBean.java
│           ├── ExamServiceBean.java
│           └── ResultServiceBean.java
│
├── university-rest/                 ← JAX-RS REST APIs
│   └── src/main/java/
│       └── com/university/rest/
│           ├── RestApplication.java
│           └── resource/
│               ├── StudentResource.java
│               ├── CourseResource.java
│               ├── EnrollmentResource.java
│               └── ResultResource.java
│
├── university-soap/                 ← JAX-WS SOAP Services
│   └── src/main/java/
│       └── com/university/soap/service/
│           ├── StudentVerificationService.java
│           ├── CourseInformationService.java
│           └── ResultVerificationService.java
│
├── university-web/                  ← JSF Web Application
│   └── src/main/
│       ├── java/com/university/web/controller/
│       │   ├── AuthBean.java
│       │   ├── StudentBean.java
│       │   ├── FacultyBean.java
│       │   ├── CourseBean.java
│       │   ├── EnrollmentBean.java
│       │   ├── ExamBean.java
│       │   └── ResultBean.java
│       └── webapp/
│           ├── login.xhtml
│           ├── admin/
│           │   ├── admin-dashboard.xhtml
│           │   ├── student-management.xhtml
│           │   ├── faculty-management.xhtml
│           │   ├── course-management.xhtml
│           │   ├── enrollment-page.xhtml
│           │   ├── exam-management.xhtml
│           │   └── results-page.xhtml
│           ├── student/
│           │   ├── student-dashboard.xhtml
│           │   ├── enrollment-page.xhtml
│           │   ├── results-page.xhtml
│           │   └── exam-schedule.xhtml
│           ├── faculty/
│           │   ├── faculty-dashboard.xhtml
│           │   ├── exam-management.xhtml
│           │   └── results-page.xhtml
│           └── resources/css/
│               └── styles.css
│
├── university-ear/                  ← EAR assembly
│   └── pom.xml
│
└── university-database/
    ├── schema.sql                   ← Complete PostgreSQL schema + seed data
    └── wildfly-datasource.xml       ← WildFly datasource config snippet
```

---

## ⚙️ Prerequisites

1. **Java 11** (OpenJDK or Oracle JDK)
2. **Maven 3.8+**
3. **WildFly 26.1.3.Final** — [Download](https://www.wildfly.org/downloads/)
4. **PostgreSQL 12+** — [Download](https://www.postgresql.org/download/)
5. **PostgreSQL JDBC Driver** — postgresql-42.x.x.jar

---

## 🚀 Step-by-Step Setup and Deployment

### Step 1: Set Up PostgreSQL Database

```sql
-- Connect to PostgreSQL as superuser
psql -U postgres

-- Create database and user
CREATE DATABASE university_db;
CREATE USER university_user WITH PASSWORD 'university_pass';
GRANT ALL PRIVILEGES ON DATABASE university_db TO university_user;
\q

-- Run the schema script
psql -U university_user -d university_db -f university-database/schema.sql
```

### Step 2: Configure WildFly

1. **Download WildFly 26.1.3.Final** and extract it.

2. **Add PostgreSQL JDBC driver module** to WildFly:
   ```
   $WILDFLY_HOME/modules/org/postgresql/main/
   ```
   Place `postgresql-42.x.x.jar` there, plus a `module.xml`:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <module xmlns="urn:jboss:module:1.3" name="org.postgresql">
       <resources>
           <resource-root path="postgresql-42.x.x.jar"/>
       </resources>
       <dependencies>
           <module name="javax.api"/>
           <module name="javax.transaction.api"/>
       </dependencies>
   </module>
   ```

3. **Add Datasource** — edit `$WILDFLY_HOME/standalone/configuration/standalone.xml`.
   Inside the `<datasources>` tag, add the content from `university-database/wildfly-datasource.xml`.

4. **Start WildFly**:
   ```bash
   # Windows
   %WILDFLY_HOME%\bin\standalone.bat
   
   # Linux/Mac
   $WILDFLY_HOME/bin/standalone.sh
   ```

### Step 3: Build the Project

```bash
cd c:\Users\sanjiv.th\Downloads\proj
mvn clean package
```

### Step 4: Deploy to WildFly

```bash
# Copy the EAR to WildFly deployments
copy university-ear\target\university-ear-1.0.0.ear %WILDFLY_HOME%\standalone\deployments\
```

Or use the WildFly CLI:
```bash
%WILDFLY_HOME%\bin\jboss-cli.bat --connect
deploy university-ear/target/university-ear-1.0.0.ear
```

---

## 🌐 Access the Application

| URL | Description |
|-----|-------------|
| `http://localhost:8080/university/` | Main application login |
| `http://localhost:8080/university/login.xhtml` | Login page |
| `http://localhost:8080/university/api/students` | REST API - Students |
| `http://localhost:8080/university/api/courses` | REST API - Courses |
| `http://localhost:8080/university/api/enrollments` | REST API - Enrollments |
| `http://localhost:8080/university/api/results` | REST API - Results |
| `http://localhost:9990` | WildFly Admin Console |

### SOAP WSDLs
After deployment, SOAP WSDLs are accessible at:
- `http://localhost:8080/university/StudentVerificationService?wsdl`
- `http://localhost:8080/university/CourseInformationService?wsdl`
- `http://localhost:8080/university/ResultVerificationService?wsdl`

---

## 🔑 Login Credentials

| Role | Email | Password |
|------|-------|----------|
| **Admin** | admin@university.edu | Admin@123 |
| **Faculty** | alan.watson@university.edu | Test@123 |
| **Faculty** | priya.sharma@university.edu | Test@123 |
| **Student** | alice.johnson@student.edu | Test@123 |
| **Student** | bob.williams@student.edu | Test@123 |

---

## 🔗 REST API Reference

### Students
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/students` | List all students |
| GET | `/api/students/{id}` | Get student by ID |
| GET | `/api/students/search?name=x` | Search students |
| POST | `/api/students` | Register student |
| PUT | `/api/students/{id}` | Update student |
| DELETE | `/api/students/{id}` | Delete student |

### Courses
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/courses` | List all courses |
| GET | `/api/courses/{id}` | Get course by ID |
| POST | `/api/courses` | Create course |
| PUT | `/api/courses/{id}` | Update course |
| DELETE | `/api/courses/{id}` | Delete course |

### Enrollments
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/enrollments` | List all enrollments |
| GET | `/api/enrollments/student/{id}` | Student's enrollments |
| POST | `/api/enrollments` | Enroll student |
| DELETE | `/api/enrollments/{id}` | Drop enrollment |

### Results
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/results` | All results |
| GET | `/api/results/student/{id}` | Student results |
| POST | `/api/results` | Publish result |
| DELETE | `/api/results/{id}` | Delete result |

---

## 🏗️ Architecture Flow

```
Browser
   │
   ▼
JSF Pages (.xhtml)
   │
   ▼
Managed Beans (@Named, @SessionScoped / @RequestScoped)
   │
   ▼
EJB Service Beans (@Stateless)     ←→   SOAP / REST Services (JAX-WS / JAX-RS)
   │
   ▼
JPA Repository (EntityManager + JPQL)
   │
   ▼
PostgreSQL Database
```

---

## 🛡️ Business Rules Implemented

1. **Enrollment Credit Limit**: Max 24 credits per semester per student
2. **Duplicate Enrollment Prevention**: Same student cannot enroll in same course twice in same semester
3. **Result Validation**: Results can only be published for enrolled students
4. **Exam Date Validation**: Exam dates cannot be in the past
5. **Email Uniqueness**: Email is enforced unique for students and faculty
6. **Password Hashing**: All passwords are SHA-256 hashed before storage
7. **Role-Based Access**: Admin/Faculty/Student see only their respective portal pages

---

## 📝 Notes

- The application uses **JTA transactions** managed by WildFly
- JSF project stage is set to **Development** for verbose error messages
- JPA is configured with `schema-generation.database.action = create` for auto table creation
- You can switch to PostgreSQL from any other supported DB by updating `persistence.xml` dialect
