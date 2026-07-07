"use client";

import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Link from "@tiptap/extension-link";
import {
  Bold,
  Italic,
  Link as LinkIcon,
  List,
  ListOrdered,
} from "lucide-react";

type TemplateEditorProps = {
  content?: string;
  onChange: (html: string) => void;
  onEditorReady?: (editor: any) => void;
};

export default function TemplateEditor({
  content = "",
  onChange,
  onEditorReady,
}: TemplateEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Link.configure({
        openOnClick: false,
      }),
    ],
    content,
    immediatelyRender: false,
    onCreate: ({ editor }) => {
      onEditorReady?.(editor);
    },
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
  });

  if (!editor) return null;

  const addLink = () => {
    const url = window.prompt("Enter URL");
    if (!url) return;
    editor.chain().focus().extendMarkRange("link").setLink({ href: url }).run();
  };

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden h-full flex flex-col">
      <div className="flex items-center gap-1 p-2 border-b border-gray-100 bg-gray-50/50">
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={`p-1.5 rounded-lg transition-colors ${
            editor.isActive("bold")
              ? "bg-gray-200 text-gray-900"
              : "hover:bg-gray-100 text-gray-500"
          }`}
        >
          <Bold size={15} />
        </button>

        <button
          type="button"
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={`p-1.5 rounded-lg transition-colors ${
            editor.isActive("italic")
              ? "bg-gray-200 text-gray-900"
              : "hover:bg-gray-100 text-gray-500"
          }`}
        >
          <Italic size={15} />
        </button>

        <button
          type="button"
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={`p-1.5 rounded-lg transition-colors ${
            editor.isActive("bulletList")
              ? "bg-gray-200 text-gray-900"
              : "hover:bg-gray-100 text-gray-500"
          }`}
        >
          <List size={15} />
        </button>

        <button
          type="button"
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={`p-1.5 rounded-lg transition-colors ${
            editor.isActive("orderedList")
              ? "bg-gray-200 text-gray-900"
              : "hover:bg-gray-100 text-gray-500"
          }`}
        >
          <ListOrdered size={15} />
        </button>

        <button
          type="button"
          onClick={addLink}
          className={`p-1.5 rounded-lg transition-colors ${
            editor.isActive("link")
              ? "bg-gray-200 text-gray-900"
              : "hover:bg-gray-100 text-gray-500"
          }`}
        >
          <LinkIcon size={15} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto cursor-text min-h-[280px]">
        <EditorContent
          editor={editor}
          className="p-4 focus:outline-none min-h-full text-sm text-gray-700 leading-relaxed"
        />
      </div>

      <div className="px-3 py-1.5 bg-gray-50 border-t border-gray-100 text-[10px] text-gray-400 text-right font-medium select-none">
        {(content || "").replace(/<[^>]*>/g, "").length} characters written
      </div>
    </div>
  );
}
