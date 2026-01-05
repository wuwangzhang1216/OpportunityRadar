"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiClient } from "@/services/api-client";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { Tabs } from "@/components/ui/tabs";
import { SharedList, SharedListDetail } from "@/types";

export default function CommunityPage() {
  const [publicLists, setPublicLists] = useState<SharedList[]>([]);
  const [myLists, setMyLists] = useState<SharedList[]>([]);
  const [featuredLists, setFeaturedLists] = useState<SharedList[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"discover" | "my-lists">("discover");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedList, setSelectedList] = useState<SharedListDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    title: "",
    description: "",
    visibility: "private" as "private" | "unlisted" | "public",
    tags: "",
  });

  useEffect(() => {
    loadLists();
  }, []);

  const loadLists = async () => {
    try {
      const [publicRes, myRes, featuredRes] = await Promise.all([
        apiClient.getPublicLists({ limit: 20 }),
        apiClient.getMyLists({ limit: 20 }),
        apiClient.getFeaturedLists(5),
      ]);
      setPublicLists(publicRes.items || []);
      setMyLists(myRes.items || []);
      setFeaturedLists(featuredRes || []);
    } catch (error) {
      console.error("Failed to load lists:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateList = async () => {
    try {
      setError(null);
      const list = await apiClient.createSharedList({
        title: formData.title,
        description: formData.description || undefined,
        visibility: formData.visibility,
        tags: formData.tags ? formData.tags.split(",").map((t) => t.trim()) : [],
      });
      setMyLists([list, ...myLists]);
      setShowCreateModal(false);
      setFormData({ title: "", description: "", visibility: "private", tags: "" });
      setActiveTab("my-lists");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create list");
    }
  };

  const handleToggleLike = async (listId: string) => {
    try {
      const result = await apiClient.toggleListLike(listId);
      // Update the list in state
      const updateList = (lists: SharedList[]) =>
        lists.map((l) =>
          l.id === listId ? { ...l, is_liked: result.is_liked, like_count: result.like_count } : l
        );
      setPublicLists(updateList(publicLists));
      setFeaturedLists(updateList(featuredLists));
    } catch (error) {
      console.error("Failed to toggle like:", error);
    }
  };

  const handleDeleteList = async (listId: string) => {
    if (!confirm("Are you sure you want to delete this list?")) return;

    try {
      await apiClient.deleteSharedList(listId);
      setMyLists(myLists.filter((l) => l.id !== listId));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete list");
    }
  };

  const handleViewList = async (slug: string) => {
    try {
      const list = await apiClient.getPublicList(slug);
      setSelectedList(list);
    } catch (error) {
      console.error("Failed to load list:", error);
    }
  };

  const visibilityIcons = {
    private: "🔒",
    unlisted: "🔗",
    public: "🌐",
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  const ListCard = ({ list, showActions = false }: { list: SharedList; showActions?: boolean }) => (
    <Card
      className="p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => handleViewList(list.slug)}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold">{list.title}</h3>
            {list.is_featured && (
              <Badge className="bg-yellow-100 text-yellow-800">Featured</Badge>
            )}
          </div>
          <p className="text-sm text-gray-500 mb-2">by {list.owner_name}</p>
          {list.description && (
            <p className="text-sm text-gray-600 line-clamp-2">{list.description}</p>
          )}
          <div className="flex flex-wrap gap-1 mt-2">
            {list.tags?.slice(0, 3).map((tag) => (
              <span key={tag} className="text-xs bg-gray-100 px-2 py-0.5 rounded">
                {tag}
              </span>
            ))}
          </div>
        </div>
        {showActions && (
          <div className="flex flex-col gap-1 ml-4" onClick={(e) => e.stopPropagation()}>
            <span className="text-sm">{visibilityIcons[list.visibility]}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDeleteList(list.id)}
              className="text-red-600"
            >
              Delete
            </Button>
          </div>
        )}
      </div>
      <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
        <span>{list.opportunity_count} opportunities</span>
        <button
          className="flex items-center gap-1 hover:text-red-500"
          onClick={(e) => {
            e.stopPropagation();
            handleToggleLike(list.id);
          }}
        >
          {list.is_liked ? "❤️" : "🤍"} {list.like_count}
        </button>
        <span>👁 {list.view_count}</span>
        <span>💬 {list.comment_count}</span>
      </div>
    </Card>
  );

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Community Lists</h1>
          <p className="text-gray-600">Discover and share curated opportunity lists</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>Create List</Button>
      </div>

      <Tabs
        tabs={[
          { id: "discover", label: "Discover" },
          { id: "my-lists", label: "My Lists" },
        ]}
        activeTab={activeTab}
        onChange={(tab) => setActiveTab(tab as "discover" | "my-lists")}
      />

      <div className="mt-6">
        {activeTab === "discover" ? (
          <div className="space-y-6">
            {featuredLists.length > 0 && (
              <div>
                <h2 className="text-lg font-semibold mb-3">Featured Lists</h2>
                <div className="grid md:grid-cols-2 gap-4">
                  {featuredLists.map((list) => (
                    <ListCard key={list.id} list={list} />
                  ))}
                </div>
              </div>
            )}

            <div>
              <h2 className="text-lg font-semibold mb-3">All Public Lists</h2>
              {publicLists.length === 0 ? (
                <Card className="p-8 text-center">
                  <p className="text-gray-500">No public lists yet. Be the first to share!</p>
                </Card>
              ) : (
                <div className="grid md:grid-cols-2 gap-4">
                  {publicLists.map((list) => (
                    <ListCard key={list.id} list={list} />
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div>
            {myLists.length === 0 ? (
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
                    d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                  />
                </svg>
                <p className="text-gray-500 mb-4">You haven&apos;t created any lists yet</p>
                <Button onClick={() => setShowCreateModal(true)}>Create Your First List</Button>
              </Card>
            ) : (
              <div className="grid md:grid-cols-2 gap-4">
                {myLists.map((list) => (
                  <ListCard key={list.id} list={list} showActions />
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create List Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => {
          setShowCreateModal(false);
          setError(null);
        }}
        title="Create a New List"
      >
        <div className="space-y-4">
          {error && (
            <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">{error}</div>
          )}

          <div>
            <label className="block text-sm font-medium mb-1">List Title *</label>
            <Input
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="My Favorite Hackathons"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="A curated collection of..."
              className="w-full px-3 py-2 border rounded-lg"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Visibility</label>
            <select
              value={formData.visibility}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  visibility: e.target.value as "private" | "unlisted" | "public",
                })
              }
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="private">🔒 Private - Only you can see</option>
              <option value="unlisted">🔗 Unlisted - Anyone with link can see</option>
              <option value="public">🌐 Public - Visible to everyone</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Tags (comma-separated)</label>
            <Input
              value={formData.tags}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
              placeholder="ai, web3, beginner-friendly"
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateList} disabled={!formData.title.trim()}>
              Create List
            </Button>
          </div>
        </div>
      </Modal>

      {/* List Detail Modal */}
      {selectedList && (
        <Modal
          isOpen={!!selectedList}
          onClose={() => setSelectedList(null)}
          title={selectedList.title}
        >
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <span>by {selectedList.owner_name}</span>
              <span>•</span>
              <span>{selectedList.opportunity_count} opportunities</span>
              <span>•</span>
              <span>❤️ {selectedList.like_count}</span>
            </div>

            {selectedList.description && (
              <p className="text-gray-600">{selectedList.description}</p>
            )}

            {selectedList.tags?.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {selectedList.tags.map((tag) => (
                  <Badge key={tag} className="bg-gray-100 text-gray-700">
                    {tag}
                  </Badge>
                ))}
              </div>
            )}

            <div className="border-t pt-4">
              <h3 className="font-medium mb-3">Opportunities</h3>
              {selectedList.opportunities?.length > 0 ? (
                <div className="space-y-2">
                  {selectedList.opportunities.map((opp) => (
                    <div key={opp.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium">{opp.title}</p>
                        <p className="text-sm text-gray-500">{opp.opportunity_type}</p>
                      </div>
                      {opp.website_url && (
                        <a
                          href={opp.website_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 text-sm hover:underline"
                        >
                          View
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No opportunities in this list yet</p>
              )}
            </div>

            {selectedList.comments?.length > 0 && (
              <div className="border-t pt-4">
                <h3 className="font-medium mb-3">Comments</h3>
                <div className="space-y-2">
                  {selectedList.comments.map((comment, i) => (
                    <div key={i} className="p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm font-medium">{comment.user_name}</p>
                      <p className="text-sm text-gray-600">{comment.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <Button onClick={() => setSelectedList(null)} className="w-full">
              Close
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
}
