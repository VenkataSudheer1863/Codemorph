package com.university.ejb.service;

import com.university.persistence.entity.Faculty;
import com.university.persistence.repository.FacultyRepository;

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
 * Stateless EJB Service Bean for Faculty business logic.
 */
@Stateless
@TransactionAttribute(TransactionAttributeType.REQUIRED)
public class FacultyServiceBean {

    @Inject
    private FacultyRepository facultyRepository;

    /**
     * Add a new faculty member.
     */
    public Faculty addFaculty(String name, String email, String department,
            String designation, String password) {
        if (name == null || name.trim().isEmpty())
            throw new IllegalArgumentException("Faculty name is required.");
        if (email == null || !email.contains("@"))
            throw new IllegalArgumentException("Invalid email address.");
        if (facultyRepository.findByEmail(email).isPresent())
            throw new IllegalArgumentException("A faculty member with this email already exists.");

        String passwordHash = hashPassword(password);
        Faculty faculty = new Faculty(name.trim(), email.trim(), department, designation, passwordHash);
        return facultyRepository.save(faculty);
    }

    /**
     * Update faculty details.
     */
    public Faculty updateFaculty(Long facultyId, String name, String department, String designation) {
        Faculty faculty = getFacultyById(facultyId);
        faculty.setName(name.trim());
        faculty.setDepartment(department);
        faculty.setDesignation(designation);
        return facultyRepository.update(faculty);
    }

    /**
     * Delete a faculty member.
     */
    public void deleteFaculty(Long facultyId) {
        facultyRepository.delete(facultyId);
    }

    /**
     * Get faculty by ID.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public Faculty getFacultyById(Long facultyId) {
        Faculty faculty = facultyRepository.findById(facultyId);
        if (faculty == null)
            throw new IllegalArgumentException("Faculty with ID " + facultyId + " not found.");
        return faculty;
    }

    /**
     * Get all faculty members.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Faculty> getAllFaculty() {
        return facultyRepository.findAll();
    }

    /**
     * Search faculty by name.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Faculty> searchFaculty(String name) {
        return facultyRepository.searchByName(name);
    }

    /**
     * Get faculty by department.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Faculty> getFacultyByDepartment(String department) {
        return facultyRepository.findByDepartment(department);
    }

    /**
     * Authenticate a faculty member.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public Optional<Faculty> authenticate(String email, String password) {
        Optional<Faculty> faculty = facultyRepository.findByEmail(email);
        if (faculty.isPresent()) {
            String hashed = hashPassword(password);
            if (hashed.equals(faculty.get().getPasswordHash())) {
                return faculty;
            }
        }
        return Optional.empty();
    }

    /**
     * Get total faculty count.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public Long getFacultyCount() {
        return facultyRepository.count();
    }

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
