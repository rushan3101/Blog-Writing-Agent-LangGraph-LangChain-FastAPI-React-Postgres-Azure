import { api } from "../../api/client";
import type { GenerateBlogRequest } from "../../types/blog";

export async function generateBlog(
  payload: GenerateBlogRequest
) {
  const response = await api.post(
    "/blogs/generate",
    payload
  );

  return response.data;
}

export async function saveBlog(
  payload: any
) {
  const response = await api.post(
    "/blogs/save",
    payload
  );

  return response.data;
}

export async function getBlogs() {
  const response = await api.get("/blogs/");

  return response.data;
}

export async function getBlog(
  id: number
) {
  const response = await api.get(
    `/blogs/${id}`
  );

  return response.data;
}

export async function streamBlog(
  payload: GenerateBlogRequest,
  onEvent: (event: any) => void
) {
  
  const baseURL = import.meta.env.VITE_API_URL
  const response =
    await fetch(
      `${baseURL}/blogs/generate-stream`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify(payload),
      }
    );

  const reader =
    response.body?.getReader();

  if (!reader) return;

  const decoder =
    new TextDecoder();

  while (true) {

    const {
      done,
      value,
    } =
      await reader.read();

    if (done) break;

    const chunk =
      decoder.decode(value);

    const lines =
      chunk
        .split("\n")
        .filter(
          line =>
            line.startsWith(
              "data:"
            )
        );

    for (const line of lines) {

      const event =
        JSON.parse(
          line.replace(
            "data: ",
            ""
          )
        );

      onEvent(event);
    }
  }
}

export async function deleteBlog(
  id: number
) {

  const response =
    await api.delete(
      `/blogs/${id}`
    );

  return response.data;
}