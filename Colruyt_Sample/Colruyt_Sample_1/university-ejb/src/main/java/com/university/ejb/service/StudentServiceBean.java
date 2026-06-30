package com.university.ejb.service;

import com.university.persistence.entity.Student;
import com.university.persistence.repository.StudentRepository;

import javax.ejb.Stateless;
import javax.ejb.TransactionAttribute;
import javax.ejb.TransactionAttributeType;
import javax.inject.Inject;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Base64;
import java.util.List;
import java.util.Optional;

/**
 * Stateless EJB Service Bean for Student business logic.
 * Handles validation, hashing, and coordination with the repository layer.
 */
@Stateless
@TransactionAttribute(TransactionAttributeType.REQUIRED)
public class StudentServiceBean {

    @Inject
    private StudentRepository studentRepository;

    /**
     * Register a new student with validation.
     */
    public Student registerStudent(String firstName, String lastName, String email,
            String department, Integer yearOfStudy, String password) {
        // Validate required fields
        if (firstName == null || firstName.trim().isEmpty())
            throw new IllegalArgumentException("First name is required.");
        if (lastName == null || lastName.trim().isEmpty())
            throw new IllegalArgumentException("Last name is required.");
        if (email == null || !email.contains("@"))
            throw new IllegalArgumentException("Invalid email address.");
        if (yearOfStudy == null || yearOfStudy < 1 || yearOfStudy > 6)
            throw new IllegalArgumentException("Year of study must be between 1 and 6.");

        // Check for duplicate email
        if (studentRepository.findByEmail(email).isPresent())
            throw new IllegalArgumentException("A student with this email already exists.");

        String passwordHash = hashPassword(password);
        Student student = new Student(firstName.trim(), lastName.trim(), email.trim(),
                department, yearOfStudy, passwordHash);
        return studentRepository.save(student);
    }

    /**
     * Update student profile details.
     */
    public Student updateStudent(Long studentId, String firstName, String lastName,
            String department, Integer yearOfStudy) {
        Student student = getStudentById(studentId);
        student.setFirstName(firstName.trim());
        student.setLastName(lastName.trim());
        student.setDepartment(department);
        student.setYearOfStudy(yearOfStudy);
        return studentRepository.update(student);
    }

    /**
     * Delete a student record.
     */
    public void deleteStudent(Long studentId) {
        studentRepository.delete(studentId);
    }

    /**
     * Find student by ID, throws exception if not found.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public Student getStudentById(Long studentId) {
        Student student = studentRepository.findById(studentId);
        if (student == null)
            throw new IllegalArgumentException("Student with ID " + studentId + " not found.");
        return student;
    }

    /**
     * Get all students.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Student> getAllStudents() {
        return studentRepository.findAll();
    }

    /**
     * Search students by name.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Student> searchStudents(String name) {
        return studentRepository.searchByName(name);
    }

    /**
     * Find students by department.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Student> getStudentsByDepartment(String department) {
        return studentRepository.findByDepartment(department);
    }

    /**
     * Authenticate a student by email and password.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public Optional<Student> authenticate(String email, String password) {
        Optional<Student> student = studentRepository.findByEmail(email);
        if (student.isPresent()) {
            String hashed = hashPassword(password);
            if (hashed.equals(student.get().getPasswordHash())) {
                return student;
            }
        }
        return Optional.empty();
    }

    /**
     * Get total student count.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public Long getStudentCount() {
        return studentRepository.count();
    }

    /**
     * Simple SHA-256 password hashing.
     */
    private String hashPassword(String password) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(password.getBytes());
            return Base64.getEncoder().encodeToString(hash);
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("Password hashing failed", e);
        }
    }
}
