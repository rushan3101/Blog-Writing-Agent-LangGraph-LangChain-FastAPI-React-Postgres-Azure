import { useState } from "react";
import { useEffect } from "react";
import type { BlogResponse, BlogListItem, StreamStep } from "./types/blog";
import { saveBlog, getBlogs, getBlog, deleteBlog} from "./features/blogs/blogApi";

import MainLayout from "./components/layout/MainLayout";
import GenerateBlogFormStream from "./features/blogs/GenerateBlogFormStream";
import BlogOutput from "./features/blogs/BlogOutput";
import ProcessingView from "./features/blogs/ProcessingView";
import Tabs from "./components/Tabs";

function App() {
  const [blog, setBlog] = useState<BlogResponse | null>(null);
  const [blogs, setBlogs] = useState<BlogListItem[]>([]);
  const [selectedBlogId,setSelectedBlogId] = useState<number>();
  const [isViewingSavedBlog,setIsViewingSavedBlog] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [activeTab, setActiveTab] = useState("Blog");

  const [steps, setSteps] = useState<StreamStep[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [deleted, setDeleted] = useState(false);

  const loadBlogs = async () => {
    try {

      const data = await getBlogs();

      setBlogs(data);

    } catch (error) {

      console.error(error);

    }
  };

  useEffect(() => {
      loadBlogs();
    }, []);

  const handleBlogSelect = async (id: number, showResultsAfterLoad = true) => {

      try {

        setShowResults(false);

        const data =
          await getBlog(id);

        setBlog(data);

        setActiveTab("Blog");

        setSelectedBlogId(id);

        setSaved(true);

        setDeleted(false);

        if (showResultsAfterLoad) {
            setIsViewingSavedBlog(true);
            setShowResults(true);
          }

      } catch (error) {

        console.error(error);

      }
  };

   const handleCreateNew = () => {

      setSteps([]);

      setBlog(null);

      setSaved(false);

      setSelectedBlogId(undefined);

      setIsViewingSavedBlog(false);

      setShowResults(false);
    };

  const handleSave = async () => {

    if (!blog) return;

    if (saved) {
        alert("Blog already saved");
        return;
      }

    try {

      setIsSaving(true);

      await saveBlog({
          topic: blog.topic ?? "Untitled Blog",

          as_of: blog.as_of,

          plan: blog.plan,

          tasks: blog.tasks,

          evidence: blog.evidence,

          images: blog.images,

          markdown: blog.markdown,

          logs: blog.logs,
        });

      await loadBlogs();

      setSaved(true);

    } catch (error) {

      console.error(error);

      alert("Failed to save blog");

    } finally {

      setIsSaving(false);

    }
  };

  const handleStreamEvent = (event: any) => {
      if (
        event.type ===
        "step_started"
      ) {

        setSteps(prev => [
            ...prev,
            {
              label: event.label,
              status: "running",
            },
          ]);
      }

      if (
        event.type ===
        "step_completed"
      ) {

        setSteps(prev =>

          prev.map(step =>

            step.label ===
            event.label

              ? {
                  ...step,

                  status:
                    "completed",
                }

              : step
          )
        );
      }

      if (
        event.type ===
        "error"
      ) {
        setSteps([{
          label: event.label,
          status: "error",
        }]);

        setTimeout(() => { setIsStreaming(false); }, 2000);
      }

      if (
        event.type ===
        "completed"
      ) {
        
        loadBlogs();

        handleBlogSelect(event.blog_id, false);

        setTimeout(() => { setShowResults(true); setIsStreaming(false); setIsViewingSavedBlog(true); }, 1000);

      }
  };

  const handleDelete = async () => {

        if (
          !selectedBlogId
        ) {
          return;
        }

        const confirmed =
          window.confirm(
            "Delete this blog?"
          );

        if (!confirmed) {
          return;
        }

        try {

          await deleteBlog(
            selectedBlogId
          );

          setDeleted(true);

          setBlog(null);
          setSelectedBlogId(undefined);
          setSaved(false);
          setIsViewingSavedBlog(false);

          await loadBlogs();

        } catch (error) {

          console.error(error);

        }
      };


  return (
    <MainLayout
      blogs={blogs}
      selectedId={selectedBlogId}
      onSelect={handleBlogSelect}
      onCreateNew={handleCreateNew}
    >
      {!isViewingSavedBlog && ( <div className="animate-fade-in"><GenerateBlogFormStream
          onLoadingChange={
            setIsStreaming
          }

          onStreamEvent={
            handleStreamEvent
          }

          isStreaming={isStreaming}
        />
        </div>
      )}    

      {isStreaming && ( <ProcessingView
          steps={steps}
        />
      )}

      {!isStreaming && showResults && blog && ( <div className="animate-fade-in"> <Tabs
        activeTab={activeTab}
        onChange={setActiveTab}
      />
      
      {activeTab === "Blog" && (
      <BlogOutput
        content={blog?.markdown}
        isLoading={isStreaming}
        onSave={handleSave}
        onDelete={handleDelete}
        isSaving={isSaving}
        isSaved={saved}
        deleted={deleted}
      />
      )}

      {activeTab === "Plan" && (
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-6 text-gray-200">
        {!blog ? (
          "Generate a blog first."
        ) : (
          <>
          <div className="text-gray-400">Topic</div>
            <h2 className="mb-4 text-2xl font-bold">
              {blog.topic}
            </h2>

            <div className="text-gray-400">Title</div>
            <h2 className="mb-4 text-2xl font-bold">
              {blog.plan?.blog_title}
            </h2>

            <div className="mb-6 grid grid-cols-3 gap-4">
              <div>
                <div className="text-gray-400">Audience</div>
                <div>{blog.plan?.audience}</div>
              </div>

              <div>
                <div className="text-gray-400">Tone</div>
                <div>{blog.plan?.tone}</div>
              </div>

              <div>
                <div className="text-gray-400">Blog Type</div>
                <div>{blog.plan?.blog_kind}</div>
              </div>
            </div>

            <div className="text-gray-400">Tasks</div>
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="p-2 text-left">ID</th>
                  <th className="p-2 text-left">Title</th>
                  <th className="p-2 text-left">Words</th>
                  <th className="p-2 text-left">Research</th>
                  <th className="p-2 text-left">Citations</th>
                  <th className="p-2 text-left">Code</th>
                </tr>
              </thead>

              <tbody>
                {blog.tasks.map((task) => (
                  <tr
                    key={task.id}
                    className="border-b border-gray-800"
                  >
                    <td className="p-2">{task.id}</td>
                    <td className="p-2">{task.title}</td>
                    <td className="p-2">{task.target_words}</td>

                    <td className="p-2">
                      {task.requires_research ? "✓" : "✗"}
                    </td>

                    <td className="p-2">
                      {task.requires_citations ? "✓" : "✗"}
                    </td>

                    <td className="p-2">
                      {task.requires_code ? "✓" : "✗"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>
      )}

      {activeTab === "Evidence" && (
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-6 text-gray-200">
        {!blog ? (
          "Generate a blog first."
        ) : (
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="p-2 text-left">S. No</th>
                <th className="p-2 text-left">Title</th>
                <th className="p-2 text-left">Source</th>
                <th className="p-2 text-left">Published</th>
              </tr>
            </thead>

            <tbody>
              {blog.evidence.map((item, idx) => (
                <tr
                  key={idx}
                  className="border-b border-gray-800"
                >
                  <td className="p-2">{idx + 1}</td>
                  <td className="p-2">{(item.title).slice(0, 70)+"..."}</td>

                  <td className="p-2">
                    <a 
                      href={item.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-500 hover:underline"
                    >
                    {item.source ?? new URL(item.url).hostname}
                    </a>
                  </td>

                  <td className="p-2">
                    {item.published_at}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      )}

      {activeTab === "Images" && (
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-6 text-gray-200">

          {!blog ? (

            "Generate a blog first."

          ) : !blog.images || blog.images.length === 0 ? (

            <div className="text-gray-400">
              No images available.
            </div>

          ) : (

            <div className="grid gap-6 md:grid-cols-2">

              {blog.images.map((image) => (

                <div
                  key={image.filename}
                  className="overflow-hidden rounded-xl border border-gray-700 bg-gray-800"
                >
                  <div className="p-4">

                    <div className="font-medium">
                      {image.caption}
                    </div>

                    <div className="mt-2 text-sm text-gray-400">
                      Alt: {image.alt}
                    </div>

                    <div className="mt-2 text-sm text-gray-400">
                      Prompt: {image.prompt}
                    </div>

                  </div>
                  
                  <img
                    src={image.image_url}
                    alt={image.alt}
                    className="w-full rounded-t-xl"
                  />

                </div>

              ))}

            </div>

          )}

        </div>
      )}

      {activeTab === "Logs" && (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-6 text-gray-200">
      {!blog ? (
        "Generate a blog first."
      ) : (
        <div className="space-y-3">
          {blog.logs.map((log, idx) => (
            <div
              key={idx}
              className="rounded-lg bg-gray-800 p-4 text-gray-200"
            >
              ✓ {log}
            </div>
          ))}
        </div>
      )}
    </div>
      )}
      </div>
      )}
    </MainLayout>
  );
}

export default App;