package com.university.persistence.repository;

import com.university.persistence.entity.Result;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;
import java.util.List;
import java.util.Optional;

/**
 * Repository (DAO) class for Result entity database operations.
 */
@Stateless
public class ResultRepository {

    @PersistenceContext(unitName = "universityPU")
    private EntityManager em;

    public Result save(Result result) {
        em.persist(result);
        em.flush();
        return result;
    }

    public Result update(Result result) {
        return em.merge(result);
    }

    public void delete(Long resultId) {
        Result result = findById(resultId);
        if (result != null) {
            em.remove(result);
        }
    }

    public Result findById(Long resultId) {
        return em.find(Result.class, resultId);
    }

    public List<Result> findAll() {
        return em.createNamedQuery("Result.findAll", Result.class).getResultList();
    }

    public List<Result> findByStudent(Long studentId) {
        return em.createNamedQuery("Result.findByStudent", Result.class)
                .setParameter("studentId", studentId)
                .getResultList();
    }

    public List<Result> findByCourse(Long courseId) {
        return em.createNamedQuery("Result.findByCourse", Result.class)
                .setParameter("courseId", courseId)
                .getResultList();
    }

    public Optional<Result> findByStudentAndCourse(Long studentId, Long courseId) {
        List<Result> results = em.createNamedQuery("Result.findByStudentAndCourse", Result.class)
                .setParameter("studentId", studentId)
                .setParameter("courseId", courseId)
                .getResultList();
        return results.isEmpty() ? Optional.empty() : Optional.of(results.get(0));
    }
}
