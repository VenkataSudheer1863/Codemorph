package com.university.persistence.repository;

import com.university.persistence.entity.Enrollment;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;
import java.util.List;
import java.util.Optional;

/**
 * Repository (DAO) class for Enrollment entity database operations.
 */
@Stateless
public class EnrollmentRepository {

    @PersistenceContext(unitName = "universityPU")
    private EntityManager em;

    public Enrollment save(Enrollment enrollment) {
        em.persist(enrollment);
        em.flush();
        return enrollment;
    }

    public Enrollment update(Enrollment enrollment) {
        return em.merge(enrollment);
    }

    public void delete(Long enrollmentId) {
        Enrollment enrollment = findById(enrollmentId);
        if (enrollment != null) {
            em.remove(enrollment);
        }
    }

    public Enrollment findById(Long enrollmentId) {
        return em.find(Enrollment.class, enrollmentId);
    }

    public List<Enrollment> findAll() {
        return em.createNamedQuery("Enrollment.findAll", Enrollment.class).getResultList();
    }

    public List<Enrollment> findByStudent(Long studentId) {
        return em.createNamedQuery("Enrollment.findByStudent", Enrollment.class)
                .setParameter("studentId", studentId)
                .getResultList();
    }

    public List<Enrollment> findByCourse(Long courseId) {
        return em.createNamedQuery("Enrollment.findByCourse", Enrollment.class)
                .setParameter("courseId", courseId)
                .getResultList();
    }

    public Optional<Enrollment> findByStudentAndCourse(Long studentId, Long courseId) {
        List<Enrollment> results = em.createNamedQuery("Enrollment.findByStudentAndCourse", Enrollment.class)
                .setParameter("studentId", studentId)
                .setParameter("courseId", courseId)
                .getResultList();
        return results.isEmpty() ? Optional.empty() : Optional.of(results.get(0));
    }

    public List<Enrollment> findByStudentAndSemester(Long studentId, String semester) {
        return em.createNamedQuery("Enrollment.findByStudentAndSemester", Enrollment.class)
                .setParameter("studentId", studentId)
                .setParameter("semester", semester)
                .getResultList();
    }

    public Long count() {
        return em.createQuery("SELECT COUNT(e) FROM Enrollment e", Long.class).getSingleResult();
    }
}
