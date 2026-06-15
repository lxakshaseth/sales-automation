"use client";

import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Link from "@tiptap/extension-link";
import { Bold, Italic, List, Link as LinkIcon } from "lucide-react";

type TemplateEditorProps = {
  content: string;
  onChange: (html: string) => void;
  onEditorReady?: (editor: any) => void;
};

export default function TemplateEditor({
  content,
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
    <div className="border border-[#d7dce5] rounded-xl overflow-hidden">
      <div className="flex gap-2 p-3 border-b border-[#eef2f7] bg-[#fafbfc]">
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleBold().run()}
          className="p-2 rounded-lg hover:bg-gray-100"
        >
          <Bold size={16} />
        </button>

        <button
          type="button"
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className="p-2 rounded-lg hover:bg-gray-100"
        >
          <Italic size={16} />
        </button>

        <button
          type="button"
          onClick={addLink}
          className="p-2 rounded-lg hover:bg-gray-100"
        >
          <LinkIcon size={16} />
        </button>
      </div>

      <div className="min-h-[350px] cursor-text">
        <EditorContent
          editor={editor}
          placeholder="Welcome [firstName] [lastName]!"
          className="min-h-[350px] p-4 focus:outline-none"
        />
      </div>
    </div>
  );
}
