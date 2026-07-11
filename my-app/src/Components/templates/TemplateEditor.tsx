"use client";

import { useEffect, useRef, useState } from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Bold, Italic, Link as LinkIcon, List, ListOrdered, Check, X, Unlink } from "lucide-react";

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
      StarterKit.configure({
        link: {
          openOnClick: false,
        },
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

  const [showLinkPopover, setShowLinkPopover] = useState(false);
  const [linkUrl, setLinkUrl] = useState("");
  const linkInputRef = useRef<HTMLInputElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (showLinkPopover) {
      linkInputRef.current?.focus();
      linkInputRef.current?.select();
    }
  }, [showLinkPopover]);

  useEffect(() => {
    if (!showLinkPopover) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setShowLinkPopover(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showLinkPopover]);

  if (!editor) return null;

  const openLinkPopover = () => {
    const existingUrl = editor.getAttributes("link").href || "";
    setLinkUrl(existingUrl);
    setShowLinkPopover(true);
  };

  const confirmLink = () => {
    const url = linkUrl.trim();
    if (!url) {
      setShowLinkPopover(false);
      return;
    }
    const href = /^https?:\/\//i.test(url) ? url : `https://${url}`;
    editor.chain().focus().extendMarkRange("link").setLink({ href }).run();
    setShowLinkPopover(false);
  };

  const removeLink = () => {
    editor.chain().focus().extendMarkRange("link").unsetLink().run();
    setShowLinkPopover(false);
  };

  const handleLinkKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      confirmLink();
    } else if (e.key === "Escape") {
      e.preventDefault();
      setShowLinkPopover(false);
    }
  };

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden h-full flex flex-col">
      <div className="relative flex items-center gap-1 p-2 border-b border-gray-100 bg-gray-50/50">
        <button
          type="button"
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={`p-1.5 rounded-lg transition-colors ${
            editor.isActive("bold") ? "bg-gray-200 text-gray-900" : "hover:bg-gray-100 text-gray-500"
          }`}
        >
          <Bold size={15} />
        </button>

        <button
          type="button"
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={`p-1.5 rounded-lg transition-colors ${
            editor.isActive("italic") ? "bg-gray-200 text-gray-900" : "hover:bg-gray-100 text-gray-500"
          }`}
        >
          <Italic size={15} />
        </button>

        <button
          type="button"
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={`p-1.5 rounded-lg transition-colors ${
            editor.isActive("bulletList") ? "bg-gray-200 text-gray-900" : "hover:bg-gray-100 text-gray-500"
          }`}
        >
          <List size={15} />
        </button>

        <button
          type="button"
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={`p-1.5 rounded-lg transition-colors ${
            editor.isActive("orderedList") ? "bg-gray-200 text-gray-900" : "hover:bg-gray-100 text-gray-500"
          }`}
        >
          <ListOrdered size={15} />
        </button>

        <button
          type="button"
          onClick={openLinkPopover}
          className={`p-1.5 rounded-lg transition-colors ${
            editor.isActive("link") ? "bg-gray-200 text-gray-900" : "hover:bg-gray-100 text-gray-500"
          }`}
        >
          <LinkIcon size={15} />
        </button>

        {showLinkPopover && (
          <div
            ref={popoverRef}
            className="absolute left-2 top-full mt-2 z-20 w-96 bg-white border border-gray-200 rounded-xl shadow-lg p-4"
          >
            <label className="block text-xs font-semibold tracking-wide text-gray-400 uppercase mb-2">
              Link URL
            </label>
            <div className="flex items-center gap-2">
              <input
                ref={linkInputRef}
                type="text"
                value={linkUrl}
                onChange={(e) => setLinkUrl(e.target.value)}
                onKeyDown={handleLinkKeyDown}
                placeholder="https://example.com"
                className="flex-1 text-base px-3 py-2.5 border border-gray-200 rounded-lg outline-none focus:border-purple-400 focus:ring-2 focus:ring-purple-100 transition-colors text-gray-700 placeholder:text-gray-300"
              />
              <button
                type="button"
                onClick={confirmLink}
                title="Apply link"
                className="p-2.5 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-colors"
              >
                <Check size={16} />
              </button>
              <button
                type="button"
                onClick={() => setShowLinkPopover(false)}
                title="Cancel"
                className="p-2.5 rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
              >
                <X size={16} />
              </button>
            </div>
            {editor.isActive("link") && (
              <button
                type="button"
                onClick={removeLink}
                className="mt-3 flex items-center gap-1.5 text-xs font-medium text-gray-400 hover:text-red-500 transition-colors"
              >
                <Unlink size={13} />
                Remove link
              </button>
            )}
          </div>
        )}
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