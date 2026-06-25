# Frontend — AI Blog Writing Agent

This frontend is the user interface for the **AI Blog Writing Agent** project. It allows a user to submit a blog topic, watch the generation process stream in real time, and explore the final blog through multiple tabs such as **Blog**, **Plan**, **Evidence**, **Images**, and **Logs**.

The frontend is built with **React + TypeScript + Vite** and styled using **Tailwind CSS**. It communicates with the FastAPI backend to trigger blog generation, fetch saved blogs, and display generated content stored by the backend.

---

# Frontend Overview

The frontend is designed around two major user flows:

1. **Generate a new blog**

   * user enters a topic and date
   * frontend starts the backend streaming generation request
   * processing steps are shown live in the UI
   * when generation completes, the saved blog is loaded and displayed in tabs

2. **View previously generated blogs**

   * sidebar lists past saved blogs
   * selecting a blog loads its full content and metadata
   * the user can browse blog content, plan, evidence, images, and logs

The frontend does **not** perform blog generation itself. It acts as the presentation and interaction layer for the LangGraph + FastAPI backend.

---

# Tech Stack

* **React** — UI rendering
* **TypeScript** — typed frontend code
* **Vite** — development server and build tool
* **Tailwind CSS** — styling
* **Axios** — standard API calls to the backend
* **Fetch / streaming handling** — for real-time generation updates

---

# Project Structure

```text id="wwod0n"
frontend/
├── .env.example
├── .gitignore
├── eslint.config.js
├── index.html
├── package.json
├── README.md
├── tsconfig.app.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
└── src/
    ├── App.css
    ├── App.tsx
    ├── index.css
    ├── main.tsx
    │
    ├── api/
    │   └── client.ts
    │
    ├── components/
    │   ├── Tabs.tsx
    │   └── layout/
    │       ├── Header.tsx
    │       ├── MainLayout.tsx
    │       └── Sidebar.tsx
    │
    ├── features/
    │   └── blogs/
    │       ├── blogApi.ts
    │       ├── BlogOutput.tsx
    │       ├── GenerateBlogFormStream.tsx
    │       └── ProcessingView.tsx
    │
    └── types/
        └── blog.ts
```

---

# Frontend Architecture

The frontend is structured around a few simple layers:

* **Layout / shared UI components**
* **Blog feature components**
* **API layer for backend communication**
* **Shared types for blog data**

This keeps the UI code separated from networking and data shape definitions.

---

# Main Files and Responsibilities

## `src/main.tsx`

Application entry point.

Responsibilities:

* bootstraps the React app
* mounts the root app component
* imports global styles

---

## `src/App.tsx`

Top-level application container.

This file coordinates the overall page state and the main user flows of the application, including:

* whether a blog is currently being generated
* which blog is selected
* whether the app is showing processing state or final results
* currently active tab
* saved blog / current blog state
* passing handlers into child components

Conceptually, `App.tsx` acts as the main orchestration layer of the frontend.

---

# API Layer

## `src/api/client.ts`

Central Axios client configuration.

Responsibilities:

* define the backend base URL using `VITE_API_URL`
* create a shared Axios instance
* ensure all normal API calls use the same backend base URL

This avoids hardcoding backend URLs across multiple components or feature files.

---

# Blog Feature Module

All blog-specific UI logic is grouped under:

```text id="y7jlwm"
src/features/blogs/
```

This keeps the project feature-oriented instead of scattering blog logic across unrelated folders.

---

## `blogApi.ts`

This file contains frontend functions for communicating with blog-related backend endpoints.

Typical responsibilities:

* fetch all saved blogs
* fetch a blog by ID
* delete a blog
* trigger / stream blog generation

This acts as the **frontend data-access layer** for the blog feature.

---

## `GenerateBlogFormStream.tsx`

This is the main **blog generation form + streaming controller** component.

Responsibilities typically include:

* rendering the “new blog” form
* collecting user input such as topic / date
* starting the streaming generation request
* reading backend stream events
* forwarding stream events upward to the parent state
* notifying the app when generation is complete

This component is central to the “generate blog” workflow.

---

## `ProcessingView.tsx`

Displays the real-time processing state while a blog is being generated.

Typical responsibilities:

* render the list of generation steps / logs
* visually show progress while the backend workflow is running
* keep the user informed before the final blog is loaded

This is what makes the UI feel interactive during long-running blog generation.

---

## `BlogOutput.tsx`

Responsible for rendering the final generated blog and its tabbed outputs.

Typical responsibilities:

* render the blog markdown output
* render the different result tabs such as Blog / Plan / Evidence / Images / Logs
* show actions like saved / delete / copy if present
* render images and structured metadata from the saved blog payload

This is the main “result display” component of the frontend.

---

# Layout Components

## `src/components/layout/MainLayout.tsx`

Defines the overall page layout structure, typically combining:

* header
* sidebar
* main content area

---

## `src/components/layout/Sidebar.tsx`

Displays the **Past Blogs** list and handles saved blog navigation.

Typical responsibilities:

* render previously generated blogs
* highlight the selected blog
* allow the user to switch between blogs

---

## `src/components/layout/Header.tsx`

Contains top-level header / title UI for the application.

---

## `src/components/Tabs.tsx`

Reusable tab-switching UI used to move between:

* Blog
* Plan
* Evidence
* Images
* Logs

This helps keep tab rendering logic separated from blog content rendering.

---

# Shared Types

## `src/types/blog.ts`

Contains TypeScript types for blog-related frontend data.

Typical examples:

* blog response shape
* image metadata shape
* plan / evidence / log structures
* generation event payloads if typed here

Keeping types centralized helps the frontend stay consistent with backend response structures.

---

# Frontend User Flow

The main frontend flow looks like this:

1. User opens the app.
2. The sidebar loads saved blogs from the backend.
3. User can either:

   * select an existing blog, or
   * create a new blog from the generation form
4. When generating a new blog:

   * the frontend starts a streaming request
   * processing steps are shown in `ProcessingView`
   * when generation completes, the frontend fetches the saved blog by ID
5. The final blog is displayed through multiple tabs.

---

# Generation + Streaming Flow

The frontend is designed to support **streaming generation updates** instead of showing only a loading spinner.

## Conceptual flow

1. User submits a new blog request.
2. Frontend sends the request to the backend streaming endpoint.
3. Backend emits progress events for major workflow steps.
4. `GenerateBlogFormStream.tsx` receives those events.
5. The current list of processing steps is updated in `App.tsx`.
6. `ProcessingView.tsx` renders those steps in real time.
7. Once generation completes, the frontend fetches the saved blog and switches to the result tabs.

This allows the UI to reflect the LangGraph workflow instead of hiding all intermediate progress.

---

# Data Flow Between Frontend and Backend

The frontend communicates with the backend in two main ways:

## 1) Standard API requests

Used for operations such as:

* fetch all blogs
* fetch blog by ID
* delete blog

These are typically handled through the shared Axios client.

## 2) Streaming generation request

Used for:

* long-running blog generation
* receiving real-time workflow progress updates
* switching from processing state to final blog view after completion

This split keeps normal CRUD operations separate from the blog-generation streaming flow.

---

# Styling

The frontend uses **Tailwind CSS** for styling, along with a small amount of component-level CSS from files such as:

* `App.css`
* `index.css`

The UI is designed around:

* a dark dashboard-like layout
* a left sidebar for past blogs
* a main content area for generation and output
* tabbed blog exploration
* a dedicated processing view for streaming steps

---

# Environment Variables

The frontend reads its backend URL from environment variables.

## Required variable

```env id="3jlwm2"
VITE_API_URL=...
```

This should point to the backend FastAPI base URL.

Example local value:

```env id="4jlwm3"
VITE_API_URL=http://localhost:8000
```

Example deployed value:

```env id="5jlwm4"
VITE_API_URL=https://your-backend-app.azurewebsites.net
```

See `.env.example` for the expected structure.

---

# Running the Frontend Locally

## 1) Go to the frontend folder

```bash id="jlwm5"
cd frontend
```

---

## 2) Create a `.env` file

Copy `.env.example` and set the backend URL:

```bash id="jlwm6"
cp .env.example .env
```

Then set:

```env id="6jlwm7"
VITE_API_URL=http://localhost:8000
```

> On Windows, if `cp` is not available, create `.env` manually using the contents of `.env.example`.

---

## 3) Install dependencies

```bash id="7jlwm8"
npm install
```

---

## 4) Run the development server

```bash id="8jlwm9"
npm run dev
```

The app will typically be available at:

```text id="9jlwm0"
http://localhost:5173
```

---

# Build for Production

To create a production build:

```bash id="0jlwm1"
npm run build
```

To preview the production build locally:

```bash id="1jlwm2"
npm run preview
```

---

# How the Frontend Fits into the Full System

This frontend is the presentation layer for the larger **AI Blog Writing Agent** system.

* **Frontend** → collects user input, displays streaming progress, and renders final blog output
* **FastAPI backend** → exposes blog APIs and invokes the graph
* **LangGraph / LangChain backend** → generates plan, content, evidence, and image instructions
* **PostgreSQL** → stores blog data and metadata
* **Azure Blob Storage** → stores generated blog images

The frontend itself remains intentionally lightweight: it does not generate content, run LLM logic, or access storage directly. Its job is to provide a clear UI over the backend workflow and persisted blog data.

---

# Notes

* The frontend expects the backend API to be running and reachable through `VITE_API_URL`.
* Blog generation is designed around a streaming workflow, so the UI state transitions are centered on **processing → completion → fetch saved blog → render tabs**.
* As the backend schema evolves, the TypeScript types in `src/types/blog.ts` should be kept in sync with backend response models.

---
