export interface GenerateBlogRequest {
  topic: string;
  as_of: string;
}

export interface Plan {
  blog_title: string;
  audience: string;
  tone: string;
  blog_kind: string;
  constraints: string[];
}

export interface Task {
  id: number;
  title: string;
  target_words: number;
  tags: string[];

  requires_research: boolean;
  requires_citations: boolean;
  requires_code: boolean;
}

export interface Evidence {
  title: string;
  url: string;
  published_at: string;
  snippet: string;
  source: string;
}

export interface BlogImage {
  placeholder: string;
  filename: string;
  alt: string;
  caption: string;
  prompt: string;
  image_url: string;
}

export interface BlogResponse {
  topic: string;
  as_of: string;
  
  plan: Plan | null;
  tasks: Task[];

  evidence: Evidence[];

  markdown: string;

  images: BlogImage[] | null;

  logs: string[];
}

export interface SaveResponse {
  message: string;
  id: number;
}

export interface BlogListItem {
  id: number;
  topic: string;
  blog_title: string;
  created_at: string;
}

export interface StreamStep {
  label: string;
  status:
    | "pending"
    | "running"
    | "completed"
    | "error";
}