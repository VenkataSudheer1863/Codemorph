package com.university.persistence.repository;

import com.university.persistence.entity.Course;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;
import java.util.List;

/**
 * Repository (DAO) class for Course entity database operations.
 */
@Stateless
public class CourseRepository {

    @PersistenceContext(unitName = "universityPU")
    private EntityManager em;

    public Course save(Course course) {
        em.persist(course);
        em.flush();
        return course;
    }

    public Course update(Course course) {
        return em.merge(course);
    }

    public void delete(Long courseId) {
        Course course = findById(courseId);
        if (course != null) {
            em.remove(course);
        }
    }

    public Course findById(Long courseId) {
        return em.find(Course.class, courseId);
    }

    public List<Course> findAll() {
        return em.createNamedQuery("Course.findAll", Course.class).getResultList();
    }

    public List<Course> findByDepartment(String department) {
        return em.createNamedQuery("Course.findByDepartment", Course.class)
                .setParameter("department", department)
                .getResultList();
    }

    public List<Course> findByFaculty(Long facultyId) {
        return em.createNamedQuery("Course.findByFaculty", Course.class)
                .setParameter("facultyId", facultyId)
                .getResultList();
    }

    public List<Course> searchByName(String name) {
        return em.createNamedQuery("Course.searchByName", Course.class)
                .setParameter("name", "%" + name.toLowerCase() + "%")
                .getResultList();
    }

    public Long count() {
        return em.createQuery("SELECT COUNT(c) FROM Course c", Long.class).getSingleResult();
    }
}
