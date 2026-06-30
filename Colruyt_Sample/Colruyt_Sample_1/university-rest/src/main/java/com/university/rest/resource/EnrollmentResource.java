package com.university.rest.resource;

import com.university.ejb.service.EnrollmentServiceBean;
import com.university.persistence.entity.Enrollment;

import javax.ejb.EJB;
import javax.ws.rs.*;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import java.util.List;

/**
 * JAX-RS REST Resource for Enrollment operations.
 */
@Path("/enrollments")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class EnrollmentResource {

    @EJB
    private EnrollmentServiceBean enrollmentService;

    /**
     * GET /api/enrollments - Get all enrollments
     */
    @GET
    public Response getAllEnrollments() {
        return Response.ok(enrollmentService.getAllEnrollments()).build();
    }

    /**
     * GET /api/enrollments/student/{studentId} - Get enrollments for a student
     */
    @GET
    @Path("/student/{studentId}")
    public Response getStudentEnrollments(@PathParam("studentId") Long studentId) {
        List<Enrollment> enrollments = enrollmentService.getStudentEnrollments(studentId);
        return Response.ok(enrollments).build();
    }

    /**
     * GET /api/enrollments/course/{courseId} - Get enrollments for a course
     */
    @GET
    @Path("/course/{courseId}")
    public Response getCourseEnrollments(@PathParam("courseId") Long courseId) {
        List<Enrollment> enrollments = enrollmentService.getCourseEnrollments(courseId);
        return Response.ok(enrollments).build();
    }

    /**
     * POST /api/enrollments - Enroll a student in a course
     */
    @POST
    public Response enrollStudent(EnrollmentRequest request) {
        try {
            Enrollment enrollment = enrollmentService.enrollStudent(
                    request.getStudentId(), request.getCourseId(), request.getSemester());
            return Response.status(Response.Status.CREATED).entity(enrollment).build();
        } catch (IllegalArgumentException e) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity("{\"error\": \"" + e.getMessage() + "\"}")
                    .build();
        }
    }

    /**
     * DELETE /api/enrollments/{id} - Drop an enrollment
     */
    @DELETE
    @Path("/{id}")
    public Response dropEnrollment(@PathParam("id") Long id) {
        enrollmentService.dropEnrollment(id);
        return Response.noContent().build();
    }

    public static class EnrollmentRequest {
        private Long studentId;
        private Long courseId;
        private String semester;

        public Long getStudentId() {
            return studentId;
        }

        public void setStudentId(Long studentId) {
            this.studentId = studentId;
        }

        public Long getCourseId() {
            return courseId;
        }

        public void setCourseId(Long courseId) {
            this.courseId = courseId;
        }

        public String getSemester() {
            return semester;
        }

        public void setSemester(String semester) {
            this.semester = semester;
        }
    }
}
