package com.university.ejb.service;

import com.university.persistence.entity.Course;
import com.university.persistence.entity.Enrollment;
import com.university.persistence.entity.Student;
import com.university.persistence.repository.CourseRepository;
import com.university.persistence.repository.EnrollmentRepository;
import com.university.persistence.repository.StudentRepository;

import javax.ejb.Stateless;
import javax.ejb.TransactionAttribute;
import javax.ejb.TransactionAttributeType;
import javax.inject.Inject;
import java.util.List;
import java.util.Optional;

/**
 * Stateless EJB Service Bean for Enrollment business logic.
 * Enforces enrollment rules: no duplicate enrollment, max credit limits.
 */
@Stateless
@TransactionAttribute(TransactionAttributeType.REQUIRED)
public class EnrollmentServiceBean {

    private static final int MAX_CREDITS_PER_SEMESTER = 24;

    @Inject
    private EnrollmentRepository enrollmentRepository;

    @Inject
    private StudentRepository studentRepository;

    @Inject
    private CourseRepository courseRepository;

    /**
     * Enroll a student in a course for a given semester.
     * Validates: student exists, course exists, not already enrolled, credit limit.
     */
    public Enrollment enrollStudent(Long studentId, Long courseId, String semester) {
        Student student = studentRepository.findById(studentId);
        if (student == null)
            throw new IllegalArgumentException("Student not found.");

        Course course = courseRepository.findById(courseId);
        if (course == null)
            throw new IllegalArgumentException("Course not found.");

        // Check duplicate enrollment
        Optional<Enrollment> existing = enrollmentRepository.findByStudentAndCourse(studentId, courseId);
        if (existing.isPresent())
            throw new IllegalArgumentException("Student is already enrolled in this course.");

        // Check max credit limit per semester
        List<Enrollment> semesterEnrollments = enrollmentRepository.findByStudentAndSemester(studentId, semester);
        int currentCredits = semesterEnrollments.stream()
                .mapToInt(e -> e.getCourse().getCredits())
                .sum();
        if (currentCredits + course.getCredits() > MAX_CREDITS_PER_SEMESTER) {
            throw new IllegalArgumentException(
                    "Enrollment would exceed the maximum credit limit of " + MAX_CREDITS_PER_SEMESTER +
                            " credits per semester. Current: " + currentCredits + ", course credits: "
                            + course.getCredits());
        }

        Enrollment enrollment = new Enrollment(student, course, semester);
        return enrollmentRepository.save(enrollment);
    }

    /**
     * Drop a course enrollment.
     */
    public void dropEnrollment(Long enrollmentId) {
        enrollmentRepository.delete(enrollmentId);
    }

    /**
     * Drop enrollment by student and course.
     */
    public void dropCourse(Long studentId, Long courseId) {
        Optional<Enrollment> enrollment = enrollmentRepository.findByStudentAndCourse(studentId, courseId);
        enrollment.ifPresent(e -> enrollmentRepository.delete(e.getEnrollmentId()));
    }

    /**
     * Get all enrollments for a student.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Enrollment> getStudentEnrollments(Long studentId) {
        return enrollmentRepository.findByStudent(studentId);
    }

    /**
     * Get all students enrolled in a course.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Enrollment> getCourseEnrollments(Long courseId) {
        return enrollmentRepository.findByCourse(courseId);
    }

    /**
     * Get all enrollments.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Enrollment> getAllEnrollments() {
        return enrollmentRepository.findAll();
    }

    /**
     * Total enrollment count.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public Long getEnrollmentCount() {
        return enrollmentRepository.count();
    }
}
