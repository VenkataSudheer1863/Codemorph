package com.university.persistence.repository;

import com.university.persistence.entity.Faculty;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;
import javax.persistence.TypedQuery;
import java.util.List;
import java.util.Optional;

/**
 * Repository (DAO) class for Faculty entity database operations.
 */
@Stateless
public class FacultyRepository {

    @PersistenceContext(unitName = "universityPU")
    private EntityManager em;

    public Faculty save(Faculty faculty) {
        em.persist(faculty);
        em.flush();
        return faculty;
    }

    public Faculty update(Faculty faculty) {
        return em.merge(faculty);
    }

    public void delete(Long facultyId) {
        Faculty faculty = findById(facultyId);
        if (faculty != null) {
            em.remove(faculty);
        }
    }

    public Faculty findById(Long facultyId) {
        return em.find(Faculty.class, facultyId);
    }

    public List<Faculty> findAll() {
        return em.createNamedQuery("Faculty.findAll", Faculty.class).getResultList();
    }

    public Optional<Faculty> findByEmail(String email) {
        TypedQuery<Faculty> query = em.createNamedQuery("Faculty.findByEmail", Faculty.class);
        query.setParameter("email", email);
        List<Faculty> results = query.getResultList();
        return results.isEmpty() ? Optional.empty() : Optional.of(results.get(0));
    }

    public List<Faculty> findByDepartment(String department) {
        return em.createNamedQuery("Faculty.findByDepartment", Faculty.class)
                .setParameter("department", department)
                .getResultList();
    }

    public List<Faculty> searchByName(String name) {
        return em.createNamedQuery("Faculty.searchByName", Faculty.class)
                .setParameter("name", "%" + name.toLowerCase() + "%")
                .getResultList();
    }

    public Long count() {
        return em.createQuery("SELECT COUNT(f) FROM Faculty f", Long.class).getSingleResult();
    }
}
