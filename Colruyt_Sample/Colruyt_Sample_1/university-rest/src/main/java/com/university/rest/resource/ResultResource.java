package com.university.rest.resource;

import com.university.ejb.service.ResultServiceBean;
import com.university.persistence.entity.Result;

import javax.ejb.EJB;
import javax.ws.rs.*;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import java.util.List;

/**
 * JAX-RS REST Resource for Result operations.
 */
@Path("/results")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class ResultResource {

    @EJB
    private ResultServiceBean resultService;

    /**
     * GET /api/results - Get all results
     */
    @GET
    public Response getAllResults() {
        return Response.ok(resultService.getAllResults()).build();
    }

    /**
     * GET /api/results/student/{studentId} - Get results for a student
     */
    @GET
    @Path("/student/{studentId}")
    public Response getStudentResults(@PathParam("studentId") Long studentId) {
        List<Result> results = resultService.getStudentResults(studentId);
        return Response.ok(results).build();
    }

    /**
     * GET /api/results/course/{courseId} - Get results for a course
     */
    @GET
    @Path("/course/{courseId}")
    public Response getCourseResults(@PathParam("courseId") Long courseId) {
        List<Result> results = resultService.getCourseResults(courseId);
        return Response.ok(results).build();
    }

    /**
     * POST /api/results - Publish a result
     */
    @POST
    public Response publishResult(ResultRequest request) {
        try {
            Result result = resultService.publishResult(
                    request.getStudentId(), request.getCourseId(), request.getGrade(),
                    request.getMarksObtained(), request.getTotalMarks(), request.getRemarks());
            return Response.status(Response.Status.CREATED).entity(result).build();
        } catch (IllegalArgumentException e) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity("{\"error\": \"" + e.getMessage() + "\"}")
                    .build();
        }
    }

    /**
     * DELETE /api/results/{id} - Delete a result
     */
    @DELETE
    @Path("/{id}")
    public Response deleteResult(@PathParam("id") Long id) {
        resultService.deleteResult(id);
        return Response.noContent().build();
    }

    public static class ResultRequest {
        private Long studentId;
        private Long courseId;
        private String grade;
        private Double marksObtained;
        private Double totalMarks;
        private String remarks;

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

        public String getGrade() {
            return grade;
        }

        public void setGrade(String grade) {
            this.grade = grade;
        }

        public Double getMarksObtained() {
            return marksObtained;
        }

        public void setMarksObtained(Double marksObtained) {
            this.marksObtained = marksObtained;
        }

        public Double getTotalMarks() {
            return totalMarks;
        }

        public void setTotalMarks(Double totalMarks) {
            this.totalMarks = totalMarks;
        }

        public String getRemarks() {
            return remarks;
        }

        public void setRemarks(String remarks) {
            this.remarks = remarks;
        }
    }
}
