import type { BlogListItem } from "../../types/blog";

interface Props {
  blogs: BlogListItem[];

  selectedId?: number;

  onSelect: (
    id: number
  ) => void;

  onCreateNew: () => void;
}

export default function Sidebar({
  blogs,
  selectedId,
  onSelect,
  onCreateNew,
}: Props) {

  return (
    <aside className="flex h-full w-72 flex-col border-r border-gray-800 bg-gray-950 p-6">

      <h2 className="mb-6 text-xl font-bold text-white">
        Blog Writing Agent
      </h2>

      <button
        onClick={onCreateNew}
        className="mb-6 w-full rounded-lg bg-blue-600 p-3 text-white hover:bg-blue-500"
      >
        + Create New Blog
      </button>

      <div className="flex min-h-0 flex-1 flex-col">

        <h3 className="mb-3 text-sm font-semibold text-gray-400">
          Past Blogs
        </h3>

        <div className="flex-1 space-y-2 overflow-y-auto pr-2">
        {blogs.map((blog) => (

          <button
            key={blog.id}
            onClick={() =>
              onSelect(blog.id)
            }
            className={`w-full rounded-lg p-3 text-left ${
              selectedId === blog.id
                ? "bg-gray-700"
                : "bg-gray-900 hover:bg-gray-800"
            }`}
          >
            <div className="text-gray-200">
              {blog.topic}
            </div>

            <div className="mt-1 text-xs text-gray-500">
              {new Date(
                blog.created_at
              ).toLocaleDateString()}
            </div>

          </button>

        ))}
        </div>

      </div>

    </aside>
  );
}