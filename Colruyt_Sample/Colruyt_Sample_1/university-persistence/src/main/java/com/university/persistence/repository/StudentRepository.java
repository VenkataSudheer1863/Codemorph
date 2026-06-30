package com.university.persistence.repository;

import com.university.persistence.entity.Student;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;
import javax.persistence.TypedQuery;
import java.util.List;
import java.util.Optional;

/**
 * Repository (DAO) class for Student entity database operations.
 * Uses JPA EntityManager with JPQL named queries.
 */
@Stateless
public class StudentRepository {

    @PersistenceContext(unitName = "universityPU")
    private EntityManager em;

    /**
     * Persist a new student entity.
     */
    public Student save(Student student) {
        em.persist(student);
        em.flush();
        return student;
    }

    /**
     * Update an existing student entity.
     */
    public Student update(Student student) {
        return em.merge(student);
    }

    /**
     * Delete a student by ID.
     */
    public void delete(Long studentId) {
        Student student = findById(studentId);
        if (student != null) {
            em.remove(student);
        }
    }

    /**
     * Find student by primary key.
     */
    public Student findById(Long studentId) {
        return em.find(Student.class, studentId);
    }

    /**
     * Find all students ordered by last name.
     */
    public List<Student> findAll() {
        return em.createNamedQuery("Student.findAll", Student.class).getResultList();
    }

    /**
     * Find student by email (unique).
     */
    public Optional<Student> findByEmail(String email) {
        TypedQuery<Student> query = em.createNamedQuery("Student.findByEmail", Student.class);
        query.setParameter("email", email);
        List<Student> results = query.getResultList();
        return results.isEmpty() ? Optional.empty() : Optional.of(results.get(0));
    }

    /**
     * Find students by department.
     */
    public List<Student> findByDepartment(String department) {
        return em.createNamedQuery("Student.findByDepartment", Student.class)
                .setParameter("department", department)
                .getResultList();
    }

    /**
     * Search students by name (first or last, case-insensitive).
     */
    public List<Student> searchByName(String name) {
        return em.createNamedQuery("Student.searchByName", Student.class)
                .setParameter("name", "%" + name.toLowerCase() + "%")
                .getResultList();
    }

    /**
     * Count total students.
     */
    public Long count() {
        return em.createQuery("SELECT COUNT(s) FROM Student s", Long.class).getSingleResult();
    }
}
