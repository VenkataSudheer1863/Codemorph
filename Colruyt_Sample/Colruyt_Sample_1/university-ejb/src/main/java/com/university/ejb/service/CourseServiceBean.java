package com.university.ejb.service;

import com.university.persistence.entity.Course;
import com.university.persistence.entity.Faculty;
import com.university.persistence.repository.CourseRepository;
import com.university.persistence.repository.FacultyRepository;

import javax.ejb.Stateless;
import javax.ejb.TransactionAttribute;
import javax.ejb.TransactionAttributeType;
import javax.inject.Inject;
import java.util.List;

/**
 * Stateless EJB Service Bean for Course management business logic.
 */
@Stateless
@TransactionAttribute(TransactionAttributeType.REQUIRED)
public class CourseServiceBean {

    @Inject
    private CourseRepository courseRepository;

    @Inject
    private FacultyRepository facultyRepository;

    /**
     * Create a new course.
     */
    public Course createCourse(String courseName, Integer credits, String department, Long facultyId) {
        if (courseName == null || courseName.trim().isEmpty())
            throw new IllegalArgumentException("Course name is required.");
        if (credits == null || credits < 1 || credits > 10)
            throw new IllegalArgumentException("Credits must be between 1 and 10.");

        Faculty faculty = null;
        if (facultyId != null) {
            faculty = facultyRepository.findById(facultyId);
            if (faculty == null)
                throw new IllegalArgumentException("Faculty with ID " + facultyId + " not found.");
        }

        Course course = new Course(courseName.trim(), credits, department, faculty);
        return courseRepository.save(course);
    }

    /**
     * Update course details.
     */
    public Course updateCourse(Long courseId, String courseName, Integer credits,
            String department, Long facultyId) {
        Course course = getCourseById(courseId);
        course.setCourseName(courseName.trim());
        course.setCredits(credits);
        course.setDepartment(department);

        if (facultyId != null) {
            Faculty faculty = facultyRepository.findById(facultyId);
            if (faculty == null)
                throw new IllegalArgumentException("Faculty not found.");
            course.setFaculty(faculty);
        } else {
            course.setFaculty(null);
        }

        return courseRepository.update(course);
    }

    /**
     * Assign a faculty member to a course.
     */
    public Course assignFaculty(Long courseId, Long facultyId) {
        Course course = getCourseById(courseId);
        Faculty faculty = facultyRepository.findById(facultyId);
        if (faculty == null)
            throw new IllegalArgumentException("Faculty not found.");
        course.setFaculty(faculty);
        return courseRepository.update(course);
    }

    /**
     * Delete a course.
     */
    public void deleteCourse(Long courseId) {
        courseRepository.delete(courseId);
    }

    /**
     * Get course by ID.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public Course getCourseById(Long courseId) {
        Course course = courseRepository.findById(courseId);
        if (course == null)
            throw new IllegalArgumentException("Course with ID " + courseId + " not found.");
        return course;
    }

    /**
     * Get all courses.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Course> getAllCourses() {
        return courseRepository.findAll();
    }

    /**
     * Get courses by department.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Course> getCoursesByDepartment(String department) {
        return courseRepository.findByDepartment(department);
    }

    /**
     * Get courses taught by a faculty member.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Course> getCoursesByFaculty(Long facultyId) {
        return courseRepository.findByFaculty(facultyId);
    }

    /**
     * Search courses by name.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Course> searchCourses(String name) {
        return courseRepository.searchByName(name);
    }

    /**
     * Total course count.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public Long getCourseCount() {
        return courseRepository.count();
    }
}
