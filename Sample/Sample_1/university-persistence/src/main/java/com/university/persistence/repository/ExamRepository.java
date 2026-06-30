package com.university.persistence.repository;

import com.university.persistence.entity.Exam;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;
import java.time.LocalDate;
import java.util.List;

/**
 * Repository (DAO) class for Exam entity database operations.
 */
@Stateless
public class ExamRepository {

    @PersistenceContext(unitName = "universityPU")
    private EntityManager em;

    public Exam save(Exam exam) {
        em.persist(exam);
        em.flush();
        return exam;
    }

    public Exam update(Exam exam) {
        return em.merge(exam);
    }

    public void delete(Long examId) {
        Exam exam = findById(examId);
        if (exam != null) {
            em.remove(exam);
        }
    }

    public Exam findById(Long examId) {
        return em.find(Exam.class, examId);
    }

    public List<Exam> findAll() {
        return em.createNamedQuery("Exam.findAll", Exam.class).getResultList();
    }

    public List<Exam> findByCourse(Long courseId) {
        return em.createNamedQuery("Exam.findByCourse", Exam.class)
                .setParameter("courseId", courseId)
                .getResultList();
    }

    public List<Exam> findUpcoming() {
        return em.createNamedQuery("Exam.findUpcoming", Exam.class)
                .setParameter("today", LocalDate.now())
                .getResultList();
    }
}
