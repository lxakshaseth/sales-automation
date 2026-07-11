"use client";

import { useState } from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Link from "@tiptap/extension-link";
import {
  Bold,
  Italic,
  Link as LinkIcon,
  List,
  ListOrdered,
  Check,
  X,
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
  const [showLinkPopup, setShowLinkPopup] = useState(false);
  const [linkUrl, setLinkUrl] = useState("");

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

  const saveLink = () => {
    if (!linkUrl.trim()) {
      editor.chain().focus().unsetLink().run();
    } else {
      editor
        .chain()
        .focus()
        .extendMarkRange("link")
        .setLink({ href: linkUrl })
        .run();
    }

    setShowLinkPopup(false);
    setLinkUrl("");
  };

  return (
    <div className="relative border border-gray-200 rounded-xl overflow-hidden h-full flex flex-col">
      {/* Toolbar */}
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
          onClick={() => {
            setLinkUrl(editor.getAttributes("link").href || "");
            setShowLinkPopup(true);
          }}
          className={`p-1.5 rounded-lg transition-colors ${
            editor.isActive("link")
              ? "bg-gray-200 text-gray-900"
              : "hover:bg-gray-100 text-gray-500"
          }`}
        >
          <LinkIcon size={15} />
        </button>
      </div>

      {/* Link Popup */}
      {showLinkPopup && (
        <div className="absolute top-14 left-3 z-50 w-96 rounded-2xl border border-gray-200 bg-white p-4 shadow-2xl">
          <label className="block text-xs font-bold uppercase tracking-wide text-gray-500 mb-2">
            Link URL
          </label>

          <div className="flex items-center gap-2">
            <input
              autoFocus
              type="url"
              value={linkUrl}
              onChange={(e) => setLinkUrl(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") saveLink();
              }}
              placeholder="https://example.com"
              className="flex-1 rounded-xl border border-violet-300 px-3 py-2 text-sm outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-100"
            />

            <button
              type="button"
              onClick={saveLink}
              className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-600 text-white hover:bg-violet-700"
            >
              <Check size={16} />
            </button>

            <button
              type="button"
              onClick={() => {
                setShowLinkPopup(false);
                setLinkUrl("");
              }}
              className="flex h-10 w-10 items-center justify-center rounded-xl text-gray-500 hover:bg-gray-100"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Editor */}
      <div className="flex-1 overflow-y-auto cursor-text min-h-[280px]">
        <EditorContent
          editor={editor}
          className="p-4 focus:outline-none min-h-full text-sm text-gray-700 leading-relaxed"
        />
      </div>

      {/* Footer */}
      <div className="px-3 py-1.5 bg-gray-50 border-t border-gray-100 text-[10px] text-gray-400 text-right font-medium select-none">
        {(content || "").replace(/<[^>]*>/g, "").length} characters written
      </div>
    </div>
  );
}
