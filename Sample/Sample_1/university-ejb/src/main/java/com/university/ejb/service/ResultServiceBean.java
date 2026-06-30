package com.university.ejb.service;

import com.university.persistence.entity.Course;
import com.university.persistence.entity.Result;
import com.university.persistence.entity.Student;
import com.university.persistence.repository.CourseRepository;
import com.university.persistence.repository.EnrollmentRepository;
import com.university.persistence.repository.ResultRepository;
import com.university.persistence.repository.StudentRepository;

import javax.ejb.Stateless;
import javax.ejb.TransactionAttribute;
import javax.ejb.TransactionAttributeType;
import javax.inject.Inject;
import java.util.List;
import java.util.Optional;

/**
 * Stateless EJB Service Bean for Result management business logic.
 * Validates that a result can only be published for an enrolled student.
 */
@Stateless
@TransactionAttribute(TransactionAttributeType.REQUIRED)
public class ResultServiceBean {

    @Inject
    private ResultRepository resultRepository;

    @Inject
    private StudentRepository studentRepository;

    @Inject
    private CourseRepository courseRepository;

    @Inject
    private EnrollmentRepository enrollmentRepository;

    /**
     * Publish a result for a student in a course.
     * Validates enrollment before allowing result upload.
     */
    public Result publishResult(Long studentId, Long courseId, String grade,
            Double marksObtained, Double totalMarks, String remarks) {
        Student student = studentRepository.findById(studentId);
        if (student == null)
            throw new IllegalArgumentException("Student not found.");

        Course course = courseRepository.findById(courseId);
        if (course == null)
            throw new IllegalArgumentException("Course not found.");

        // Business rule: Student must be enrolled to get a result
        if (enrollmentRepository.findByStudentAndCourse(studentId, courseId).isEmpty())
            throw new IllegalArgumentException("Student is not enrolled in this course. Cannot publish result.");

        // Validate grade
        if (grade == null || grade.trim().isEmpty())
            throw new IllegalArgumentException("Grade is required.");

        // Check if result already exists — update if present
        Optional<Result> existingResult = resultRepository.findByStudentAndCourse(studentId, courseId);
        if (existingResult.isPresent()) {
            Result result = existingResult.get();
            result.setGrade(grade.trim());
            result.setMarksObtained(marksObtained);
            result.setTotalMarks(totalMarks);
            result.setRemarks(remarks);
            return resultRepository.update(result);
        }

        Result result = new Result(student, course, grade.trim(), marksObtained, totalMarks);
        result.setRemarks(remarks);
        return resultRepository.save(result);
    }

    /**
     * Delete a result.
     */
    public void deleteResult(Long resultId) {
        resultRepository.delete(resultId);
    }

    /**
     * Get result by ID.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public Result getResultById(Long resultId) {
        Result result = resultRepository.findById(resultId);
        if (result == null)
            throw new IllegalArgumentException("Result not found.");
        return result;
    }

    /**
     * Get all results for a student.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Result> getStudentResults(Long studentId) {
        return resultRepository.findByStudent(studentId);
    }

    /**
     * Get all results for a course.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Result> getCourseResults(Long courseId) {
        return resultRepository.findByCourse(courseId);
    }

    /**
     * Get all results.
     */
    @TransactionAttribute(TransactionAttributeType.SUPPORTS)
    public List<Result> getAllResults() {
        return resultRepository.findAll();
    }
}
