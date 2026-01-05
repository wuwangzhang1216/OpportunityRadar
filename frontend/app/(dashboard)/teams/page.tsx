"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/services/api-client";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { Team, TeamRole } from "@/types";

export default function TeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [newTeamName, setNewTeamName] = useState("");
  const [newTeamDescription, setNewTeamDescription] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<TeamRole>("member");
  const [joinCode, setJoinCode] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    try {
      const response = await apiClient.getMyTeams();
      setTeams(response.items || response || []);
    } catch (error) {
      console.error("Failed to load teams:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTeam = async () => {
    if (!newTeamName.trim()) return;

    try {
      setError(null);
      const team = await apiClient.createTeam({
        name: newTeamName,
        description: newTeamDescription || undefined,
      });
      setTeams([...teams, team]);
      setShowCreateModal(false);
      setNewTeamName("");
      setNewTeamDescription("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create team");
    }
  };

  const handleInvite = async () => {
    if (!selectedTeam || !inviteEmail.trim()) return;

    try {
      setError(null);
      await apiClient.inviteToTeam(selectedTeam.id, inviteEmail, inviteRole);
      setShowInviteModal(false);
      setInviteEmail("");
      loadTeams(); // Reload to get updated invite list
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to send invite");
    }
  };

  const handleJoinTeam = async () => {
    if (!joinCode.trim()) return;

    try {
      setError(null);
      await apiClient.joinTeam(joinCode);
      setShowJoinModal(false);
      setJoinCode("");
      loadTeams();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Invalid invite code");
    }
  };

  const handleLeaveTeam = async (teamId: string) => {
    if (!confirm("Are you sure you want to leave this team?")) return;

    try {
      await apiClient.leaveTeam(teamId);
      setTeams(teams.filter((t) => t.id !== teamId));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to leave team");
    }
  };

  const getRoleBadgeColor = (role: TeamRole) => {
    switch (role) {
      case "owner":
        return "bg-purple-100 text-purple-800";
      case "admin":
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
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
        <h1 className="text-2xl font-bold">Teams</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowJoinModal(true)}>
            Join Team
          </Button>
          <Button onClick={() => setShowCreateModal(true)}>Create Team</Button>
        </div>
      </div>

      {teams.length === 0 ? (
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
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
          <p className="text-gray-500 mb-4">You&apos;re not part of any teams yet</p>
          <div className="flex justify-center gap-2">
            <Button variant="outline" onClick={() => setShowJoinModal(true)}>
              Join a Team
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>Create a Team</Button>
          </div>
        </Card>
      ) : (
        <div className="grid gap-4">
          {teams.map((team) => (
            <Card key={team.id} className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-xl font-semibold">{team.name}</h2>
                  {team.description && (
                    <p className="text-gray-600 mt-1">{team.description}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedTeam(team);
                      setShowInviteModal(true);
                    }}
                  >
                    Invite
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleLeaveTeam(team.id)}
                  >
                    Leave
                  </Button>
                </div>
              </div>

              <div className="mt-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">
                  Members ({team.members?.length || 0})
                </h3>
                <div className="flex flex-wrap gap-2">
                  {team.members?.map((member) => (
                    <div
                      key={member.user_id}
                      className="flex items-center gap-2 bg-gray-50 px-3 py-1.5 rounded-full"
                    >
                      <span className="text-sm">{member.full_name || member.email}</span>
                      <Badge className={`text-xs ${getRoleBadgeColor(member.role)}`}>
                        {member.role}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>

              {team.pending_invites && team.pending_invites.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">
                    Pending Invites ({team.pending_invites.length})
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {team.pending_invites.map((invite) => (
                      <div
                        key={invite.id}
                        className="flex items-center gap-2 bg-yellow-50 px-3 py-1.5 rounded-full"
                      >
                        <span className="text-sm text-yellow-800">{invite.email}</span>
                        <span className="text-xs text-yellow-600">(pending)</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {team.shared_opportunities && team.shared_opportunities.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">
                    Shared Opportunities ({team.shared_opportunities.length})
                  </h3>
                  <p className="text-sm text-gray-500">
                    {team.shared_opportunities.length} opportunities shared with this team
                  </p>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* Create Team Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => {
          setShowCreateModal(false);
          setError(null);
        }}
        title="Create a New Team"
      >
        <div className="space-y-4">
          {error && (
            <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">
              {error}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium mb-1">Team Name</label>
            <Input
              value={newTeamName}
              onChange={(e) => setNewTeamName(e.target.value)}
              placeholder="My Awesome Team"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Description (optional)</label>
            <Input
              value={newTeamDescription}
              onChange={(e) => setNewTeamDescription(e.target.value)}
              placeholder="A team for hackathon enthusiasts"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateTeam} disabled={!newTeamName.trim()}>
              Create Team
            </Button>
          </div>
        </div>
      </Modal>

      {/* Invite Modal */}
      <Modal
        isOpen={showInviteModal}
        onClose={() => {
          setShowInviteModal(false);
          setError(null);
        }}
        title={`Invite to ${selectedTeam?.name}`}
      >
        <div className="space-y-4">
          {error && (
            <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">
              {error}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium mb-1">Email Address</label>
            <Input
              type="email"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="teammate@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Role</label>
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value as TeamRole)}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="member">Member</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowInviteModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleInvite} disabled={!inviteEmail.trim()}>
              Send Invite
            </Button>
          </div>
        </div>
      </Modal>

      {/* Join Team Modal */}
      <Modal
        isOpen={showJoinModal}
        onClose={() => {
          setShowJoinModal(false);
          setError(null);
        }}
        title="Join a Team"
      >
        <div className="space-y-4">
          {error && (
            <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">
              {error}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium mb-1">Invite Code</label>
            <Input
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value)}
              placeholder="Enter your invite code"
            />
            <p className="text-sm text-gray-500 mt-1">
              Ask your team admin for an invite code
            </p>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowJoinModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleJoinTeam} disabled={!joinCode.trim()}>
              Join Team
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
