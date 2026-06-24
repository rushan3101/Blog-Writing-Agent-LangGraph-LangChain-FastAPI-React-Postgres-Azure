import type { ReactNode } from "react";
import Sidebar from "./Sidebar";
import Header from "./Header";
import type {BlogListItem} from "../../types/blog";

interface Props {
  children: ReactNode;

  blogs: BlogListItem[];

  selectedId?: number;

  onSelect: (
    id: number
  ) => void;

  onCreateNew: () => void;
}

export default function MainLayout({
  children,
  blogs,
  selectedId,
  onSelect,
  onCreateNew,
}: Props) {
  return (
    <div className="flex h-screen bg-gray-950">
      <Sidebar
        blogs={blogs}
        selectedId={selectedId}
        onSelect={onSelect}
        onCreateNew={onCreateNew}
      />

      <div className="flex flex-1 flex-col">
        <Header />

        <main className="flex-1 overflow-auto p-8">
          {children}
        </main>
      </div>
    </div>
  );
}