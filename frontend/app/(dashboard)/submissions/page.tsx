"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/services/api-client";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { OpportunitySubmission, SubmissionStatus } from "@/types";

const statusColors: Record<SubmissionStatus, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  needs_info: "bg-blue-100 text-blue-800",
};

const statusLabels: Record<SubmissionStatus, string> = {
  pending: "Pending Review",
  approved: "Approved",
  rejected: "Rejected",
  needs_info: "Needs More Info",
};

export default function SubmissionsPage() {
  const [submissions, setSubmissions] = useState<OpportunitySubmission[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedSubmission, setSelectedSubmission] = useState<OpportunitySubmission | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [enhancing, setEnhancing] = useState(false);
  const [suggestions, setSuggestions] = useState<any>(null);

  const [formData, setFormData] = useState({
    title: "",
    description: "",
    website_url: "",
    host_name: "",
    opportunity_type: "hackathon",
    format: "",
    themes: "",
    technologies: "",
    application_deadline: "",
    event_start_date: "",
    event_end_date: "",
    total_prize_value: "",
    team_size_min: "",
    team_size_max: "",
    eligibility_notes: "",
  });

  useEffect(() => {
    loadSubmissions();
  }, []);

  const loadSubmissions = async () => {
    try {
      const response = await apiClient.getMySubmissions();
      setSubmissions(response.items || []);
    } catch (error) {
      console.error("Failed to load submissions:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      setError(null);
      const data = {
        ...formData,
        themes: formData.themes ? formData.themes.split(",").map((t) => t.trim()) : [],
        technologies: formData.technologies ? formData.technologies.split(",").map((t) => t.trim()) : [],
        total_prize_value: formData.total_prize_value ? parseFloat(formData.total_prize_value) : undefined,
        team_size_min: formData.team_size_min ? parseInt(formData.team_size_min) : undefined,
        team_size_max: formData.team_size_max ? parseInt(formData.team_size_max) : undefined,
        application_deadline: formData.application_deadline || undefined,
        event_start_date: formData.event_start_date || undefined,
        event_end_date: formData.event_end_date || undefined,
        format: formData.format || undefined,
        eligibility_notes: formData.eligibility_notes || undefined,
      };

      const submission = await apiClient.createSubmission(data);
      setSubmissions([submission, ...submissions]);
      setShowCreateModal(false);
      resetForm();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to submit opportunity");
    }
  };

  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      website_url: "",
      host_name: "",
      opportunity_type: "hackathon",
      format: "",
      themes: "",
      technologies: "",
      application_deadline: "",
      event_start_date: "",
      event_end_date: "",
      total_prize_value: "",
      team_size_min: "",
      team_size_max: "",
      eligibility_notes: "",
    });
  };

  const handleEnhance = async (submissionId: string) => {
    try {
      setEnhancing(true);
      const response = await apiClient.enhanceSubmission(submissionId);
      setSuggestions(response.suggestions);
    } catch (error) {
      console.error("Failed to enhance submission:", error);
    } finally {
      setEnhancing(false);
    }
  };

  const handleDelete = async (submissionId: string) => {
    if (!confirm("Are you sure you want to delete this submission?")) return;

    try {
      await apiClient.deleteSubmission(submissionId);
      setSubmissions(submissions.filter((s) => s.id !== submissionId));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete submission");
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">My Submissions</h1>
          <p className="text-gray-600">Submit opportunities you find for review</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>Submit Opportunity</Button>
      </div>

      {submissions.length === 0 ? (
        <Card className="p-12 text-center">
          <svg
            className="w-16 h-16 text-gray-300 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p className="text-gray-500 mb-4">You haven&apos;t submitted any opportunities yet</p>
          <Button onClick={() => setShowCreateModal(true)}>Submit Your First Opportunity</Button>
        </Card>
      ) : (
        <div className="space-y-4">
          {submissions.map((submission) => (
            <Card key={submission.id} className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h2 className="text-lg font-semibold">{submission.title}</h2>
                    <Badge className={statusColors[submission.status]}>
                      {statusLabels[submission.status]}
                    </Badge>
                  </div>
                  <p className="text-gray-600 text-sm mb-2">{submission.host_name}</p>
                  <p className="text-gray-500 text-sm line-clamp-2">{submission.description}</p>

                  <div className="flex flex-wrap gap-2 mt-3">
                    <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                      {submission.opportunity_type}
                    </span>
                    {submission.themes?.slice(0, 3).map((theme) => (
                      <span key={theme} className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">
                        {theme}
                      </span>
                    ))}
                  </div>

                  {submission.review_notes && submission.review_notes.length > 0 && (
                    <div className="mt-4 bg-gray-50 p-3 rounded-lg">
                      <p className="text-sm font-medium text-gray-700">Latest Review Note:</p>
                      <p className="text-sm text-gray-600">
                        {submission.review_notes[submission.review_notes.length - 1].note}
                      </p>
                    </div>
                  )}
                </div>

                <div className="flex flex-col gap-2 ml-4">
                  {submission.status === "pending" && (
                    <>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEnhance(submission.id)}
                        disabled={enhancing}
                      >
                        {enhancing ? "Enhancing..." : "AI Enhance"}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(submission.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        Delete
                      </Button>
                    </>
                  )}
                  <a
                    href={submission.website_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:underline"
                  >
                    View Site
                  </a>
                </div>
              </div>

              <div className="flex items-center gap-4 mt-4 text-xs text-gray-500">
                <span>Submitted {formatDate(submission.created_at)}</span>
                {submission.application_deadline && (
                  <span>Deadline: {formatDate(submission.application_deadline)}</span>
                )}
                {submission.total_prize_value && (
                  <span>Prize: ${submission.total_prize_value.toLocaleString()}</span>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Submission Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => {
          setShowCreateModal(false);
          setError(null);
          resetForm();
        }}
        title="Submit an Opportunity"
      >
        <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-2">
          {error && (
            <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Title *</label>
              <Input
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="Hackathon Name"
              />
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Description *</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Describe the opportunity..."
                className="w-full px-3 py-2 border rounded-lg min-h-[100px]"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Website URL *</label>
              <Input
                value={formData.website_url}
                onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
                placeholder="https://..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Host/Organizer *</label>
              <Input
                value={formData.host_name}
                onChange={(e) => setFormData({ ...formData, host_name: e.target.value })}
                placeholder="Company or organization"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Type</label>
              <select
                value={formData.opportunity_type}
                onChange={(e) => setFormData({ ...formData, opportunity_type: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="hackathon">Hackathon</option>
                <option value="grant">Grant</option>
                <option value="competition">Competition</option>
                <option value="bounty">Bounty</option>
                <option value="accelerator">Accelerator</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Format</label>
              <select
                value={formData.format}
                onChange={(e) => setFormData({ ...formData, format: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="">Select format</option>
                <option value="online">Online</option>
                <option value="in-person">In-Person</option>
                <option value="hybrid">Hybrid</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Themes (comma-separated)</label>
              <Input
                value={formData.themes}
                onChange={(e) => setFormData({ ...formData, themes: e.target.value })}
                placeholder="AI, Web3, Climate"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Technologies</label>
              <Input
                value={formData.technologies}
                onChange={(e) => setFormData({ ...formData, technologies: e.target.value })}
                placeholder="Python, React, AWS"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Application Deadline</label>
              <Input
                type="datetime-local"
                value={formData.application_deadline}
                onChange={(e) => setFormData({ ...formData, application_deadline: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Total Prize Value ($)</label>
              <Input
                type="number"
                value={formData.total_prize_value}
                onChange={(e) => setFormData({ ...formData, total_prize_value: e.target.value })}
                placeholder="10000"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Event Start Date</label>
              <Input
                type="datetime-local"
                value={formData.event_start_date}
                onChange={(e) => setFormData({ ...formData, event_start_date: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Event End Date</label>
              <Input
                type="datetime-local"
                value={formData.event_end_date}
                onChange={(e) => setFormData({ ...formData, event_end_date: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Min Team Size</label>
              <Input
                type="number"
                value={formData.team_size_min}
                onChange={(e) => setFormData({ ...formData, team_size_min: e.target.value })}
                placeholder="1"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Max Team Size</label>
              <Input
                type="number"
                value={formData.team_size_max}
                onChange={(e) => setFormData({ ...formData, team_size_max: e.target.value })}
                placeholder="5"
              />
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Eligibility Notes</label>
              <textarea
                value={formData.eligibility_notes}
                onChange={(e) => setFormData({ ...formData, eligibility_notes: e.target.value })}
                placeholder="Any eligibility requirements..."
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!formData.title || !formData.description || !formData.website_url || !formData.host_name}
            >
              Submit for Review
            </Button>
          </div>
        </div>
      </Modal>

      {/* AI Suggestions Modal */}
      {suggestions && (
        <Modal
          isOpen={!!suggestions}
          onClose={() => setSuggestions(null)}
          title="AI Enhancement Suggestions"
        >
          <div className="space-y-4">
            {suggestions.suggested_themes && (
              <div>
                <p className="font-medium">Suggested Themes:</p>
                <p className="text-gray-600">{suggestions.suggested_themes}</p>
              </div>
            )}
            {suggestions.suggested_technologies && (
              <div>
                <p className="font-medium">Suggested Technologies:</p>
                <p className="text-gray-600">{suggestions.suggested_technologies}</p>
              </div>
            )}
            {suggestions.short_description && (
              <div>
                <p className="font-medium">Suggested Short Description:</p>
                <p className="text-gray-600">{suggestions.short_description}</p>
              </div>
            )}
            {suggestions.missing_info && (
              <div>
                <p className="font-medium">Missing Information:</p>
                <p className="text-gray-600">{suggestions.missing_info}</p>
              </div>
            )}
            {suggestions.raw_response && (
              <div>
                <p className="font-medium">AI Response:</p>
                <p className="text-gray-600 whitespace-pre-wrap">{suggestions.raw_response}</p>
              </div>
            )}
            <Button onClick={() => setSuggestions(null)}>Close</Button>
          </div>
        </Modal>
      )}
    </div>
  );
}
