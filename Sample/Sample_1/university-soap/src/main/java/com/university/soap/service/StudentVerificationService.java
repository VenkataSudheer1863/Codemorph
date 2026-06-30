package com.university.soap.service;

import com.university.ejb.service.StudentServiceBean;
import com.university.persistence.entity.Student;

import javax.ejb.EJB;
import javax.jws.WebMethod;
import javax.jws.WebParam;
import javax.jws.WebResult;
import javax.jws.WebService;
import java.util.Optional;

/**
 * JAX-WS SOAP Web Service for Student verification.
 * Used for legacy system integration — verifies student identity.
 */
@WebService(name = "StudentVerificationService", serviceName = "StudentVerificationService", portName = "StudentVerificationPort", targetNamespace = "http://soap.university.com/student")
public class StudentVerificationService {

    @EJB
    private StudentServiceBean studentService;

    /**
     * Verify if a student exists by email.
     */
    @WebMethod(operationName = "verifyStudentByEmail")
    @WebResult(name = "verified")
    public boolean verifyStudentByEmail(@WebParam(name = "email") String email) {
        return studentService.getAllStudents().stream()
                .anyMatch(s -> s.getEmail().equalsIgnoreCase(email));
    }

    /**
     * Get student details by ID for verification purposes.
     */
    @WebMethod(operationName = "getStudentInfo")
    @WebResult(name = "studentInfo")
    public StudentInfo getStudentInfo(@WebParam(name = "studentId") Long studentId) {
        try {
            Student student = studentService.getStudentById(studentId);
            return new StudentInfo(student.getStudentId(), student.getFullName(),
                    student.getEmail(), student.getDepartment(),
                    student.getYearOfStudy());
        } catch (IllegalArgumentException e) {
            return null;
        }
    }

    /**
     * Authenticate a student via SOAP (for external integrations).
     */
    @WebMethod(operationName = "authenticateStudent")
    @WebResult(name = "authResult")
    public AuthResult authenticateStudent(@WebParam(name = "email") String email,
            @WebParam(name = "password") String password) {
        Optional<Student> result = studentService.authenticate(email, password);
        if (result.isPresent()) {
            Student s = result.get();
            return new AuthResult(true, s.getStudentId(), s.getFullName(), "STUDENT");
        }
        return new AuthResult(false, null, null, null);
    }

    // ===== SOAP Transfer Objects =====

    public static class StudentInfo {
        public Long studentId;
        public String fullName;
        public String email;
        public String department;
        public Integer yearOfStudy;

        public StudentInfo() {
        }

        public StudentInfo(Long studentId, String fullName, String email,
                String department, Integer yearOfStudy) {
            this.studentId = studentId;
            this.fullName = fullName;
            this.email = email;
            this.department = department;
            this.yearOfStudy = yearOfStudy;
        }
    }

    public static class AuthResult {
        public boolean success;
        public Long userId;
        public String userName;
        public String role;

        public AuthResult() {
        }

        public AuthResult(boolean success, Long userId, String userName, String role) {
            this.success = success;
            this.userId = userId;
            this.userName = userName;
            this.role = role;
        }
    }
}
