"use client";

import { useState, useEffect, createContext, useContext } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Contact,
  LayoutTemplate,
  Megaphone,
  Menu,
  ChevronLeft,
  Rocket,
  Search,
  ChevronDown,
  MessageCircle,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface SidebarSubItem {
  name: string;
  href: string;
  notificationId?: string;
  icon?: LucideIcon;
}

interface SidebarMenuItem {
  name: string;
  href?: string;
  icon: LucideIcon;
  items?: SidebarSubItem[];
  notificationId?: string;
}

interface SidebarContextValue {
  isCollapsed: boolean;
  toggleCollapse: () => void;
}

const SidebarContext = createContext<SidebarContextValue | undefined>(
  undefined,
);

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const toggleCollapse = () => setIsCollapsed((prev) => !prev);
  const isAuthRoute =
    pathname === "/" || pathname === "/sign-in" || pathname === "/sign-up";

  return (
    <SidebarContext.Provider value={{ isCollapsed, toggleCollapse }}>
      {!isAuthRoute && (
        <Sidebar isCollapsed={isCollapsed} onToggleCollapse={toggleCollapse} />
      )}
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within SidebarProvider");
  }
  return context;
}

const menu: SidebarMenuItem[] = [
  { name: "Dashboard", href: "/Dashboard", icon: LayoutDashboard },
  { name: "Campaigns", href: "/Campaign", icon: Megaphone },
  { name: "Contacts", href: "/Contacts", icon: Contact },
  { name: "Templates", href: "/templates", icon: LayoutTemplate },
  { name: "WhatsApp", href: "/whatsapp", icon: MessageCircle },
];
interface SidebarItemProps {
  item: SidebarMenuItem;
  count: number;
  isCollapsed: boolean;
  isPermanentlyCollapsed: boolean;
  pathname: string;
  hoveredItem: {
    id: string;
    top: number;
  } | null;

  setHoveredItem: (
    value: {
      id: string;
      top: number;
    } | null,
  ) => void;
  onClick: (e: React.MouseEvent<HTMLAnchorElement>, href: string) => void;
  onToggleCollapse?: () => void;
}

function SidebarItem({
  item,
  count,
  isCollapsed,
  isPermanentlyCollapsed,
  pathname,
  hoveredItem,
  setHoveredItem,
  onClick,
  onToggleCollapse,
}: SidebarItemProps) {
  const Icon = item.icon;
  const [isExpanded, setIsExpanded] = useState(false);

  const hasSubmenu = Boolean(item.items && item.items.length > 0);

  // Check active state
  const isChildActive = hasSubmenu
    ? item.items?.some((sub) => pathname === sub.href)
    : false;

  const isActive = item.href ? pathname === item.href : isChildActive;

  const handleParentClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (hasSubmenu) {
      e.preventDefault();
      if (isPermanentlyCollapsed && onToggleCollapse) {
        onToggleCollapse();
        setTimeout(() => setIsExpanded(true), 150);
      } else {
        setIsExpanded(!isExpanded);
      }
    } else if (item.href) {
      onClick(e, item.href);
    }
  };

  return (
    <>
      <Link
        onMouseEnter={(e) => {
          if (!isCollapsed || isActive) return;

          const rect = e.currentTarget.getBoundingClientRect();

          setHoveredItem({
            id: item.name,
            top: rect.top + rect.height / 2,
          });
        }}
        onMouseLeave={() => setHoveredItem(null)}
        href={item.href || "#"}
        onClick={handleParentClick}
        className={`relative group rounded-2xl flex items-center min-h-12 ${
          isCollapsed ? "justify-center" : "justify-start"
        }`}
      >
        {/* Active Background */}
        {isActive && (
          <motion.div
            layoutId="active-pill"
            className="absolute inset-0 bg-linear-to-r from-violet-600 to-purple-600 rounded-2xl"
            transition={{
              type: "spring",
              stiffness: 260,
              damping: 28,
            }}
          />
        )}

        <div
          className={`relative z-10 flex items-center gap-3.5 px-4 py-3 group ${
            isCollapsed ? "justify-center w-full px-0" : "w-full"
          }`}
        >
          <Icon
            className={`w-5 h-5 shrink-0 transition-all ${
              isActive
                ? "text-white"
                : "text-slate-400 group-hover:text-violet-600"
            }`}
            strokeWidth={isActive ? 2.5 : 2}
          />
          {/* Smooth label animation */}
          <AnimatePresence>
            {!isCollapsed && (
              <motion.span
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: "auto" }}
                exit={{ opacity: 0, width: 0 }}
                transition={{ duration: 0.2 }}
                className={`text-sm font-medium whitespace-nowrap overflow-hidden flex-1 ${
                  isActive
                    ? "text-white font-semibold"
                    : "text-slate-600 group-hover:text-slate-900"
                }`}
              >
                {item.name}
              </motion.span>
            )}
          </AnimatePresence>
          {!isCollapsed && hasSubmenu && (
            <ChevronDown
              className={`w-4 h-4 shrink-0 transition-transform duration-200 ${
                isActive ? "text-white/80" : "text-slate-400"
              } ${isExpanded ? "rotate-180" : ""}`}
            />
          )}

          {count > 0 && (
            <div
              className={`absolute ${isCollapsed ? "top-1 right-1" : "right-10"} flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white ring-2 ring-white`}
            >
              {count}
            </div>
          )}
        </div>

        {isCollapsed && hoveredItem && (
          <motion.div
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -6 }}
            transition={{ duration: 0.15 }}
            className="fixed left-[73px] z-[99999]"
            style={{
              top: hoveredItem.top,
              transform: "translateY(-50%)",
            }}
          >
            <div className="relative flex items-center">
              {/* Arrow */}
              <div
                className="
                absolute
                -left-[7px]
                top-1/2
                -translate-y-1/2
                w-0
                h-0
                border-t-[7px]
                border-b-[7px]
                border-r-[8px]
                border-t-transparent
                border-b-transparent
                border-r-violet-600
              "
              />

              {/* Label */}
              <div
                className="
                  relative
                  bg-violet-600
                  text-white
                  text-xs
                  font-medium
                  px-3
                  py-2
                  rounded-lg
                  shadow-xl
                  whitespace-nowrap  
                "
              >
                {hoveredItem.id}
              </div>
            </div>
          </motion.div>
        )}
      </Link>

      {/* Submenu */}
      <AnimatePresence>
        {hasSubmenu && isExpanded && !isCollapsed && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="py-1 space-y-0.5">
              {item.items?.map((sub) => {
                const isSubActive = pathname === sub.href;
                const SubIcon = sub.icon;
                return (
                  <Link
                    key={sub.href}
                    href={sub.href}
                    onClick={(e) => onClick(e, sub.href)}
                    className={`flex items-center pl-4 pr-4 py-2.5 text-sm transition-colors rounded-xl mx-2 group/sub ${
                      isSubActive
                        ? "text-violet-600 font-medium bg-violet-50"
                        : "text-slate-500 hover:text-slate-900 hover:bg-slate-50"
                    }`}
                  >
                    <div className="w-5 h-5 mr-3.5 flex items-center justify-center">
                      {SubIcon ? (
                        <SubIcon
                          className={`w-4 h-4 shrink-0 transition-colors ${isSubActive ? "text-violet-600" : "text-slate-400 group-hover/sub:text-slate-600"}`}
                        />
                      ) : (
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${isSubActive ? "bg-violet-600" : "bg-slate-300"}`}
                        />
                      )}
                    </div>
                    {sub.name}
                  </Link>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

interface SidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  onHover?: (isHovered: boolean) => void;
}

export default function Sidebar({
  isCollapsed,
  onToggleCollapse,
  onHover,
}: SidebarProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [hoveredItem, setHoveredItem] = useState<{
    id: string;
    top: number;
  } | null>(null);
  const pathname = usePathname();
  const router = useRouter();
  const [isMobile, setIsMobile] = useState(false);
  const [isHovering, setIsHovering] = useState(false);
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  const handleNavigation = (
    e: React.MouseEvent<HTMLAnchorElement>,
    href: string,
  ) => {
    e.preventDefault();
    setHoveredItem(null);
    router.push(href);
    if (isMobile && !isCollapsed) {
      onToggleCollapse();
    }
  };

  // Flatten menu for search, preserve hierarchy otherwise
  const displayMenu = searchQuery
    ? menu.reduce((acc: SidebarMenuItem[], item) => {
        // Parent match
        if (item.name.toLowerCase().includes(searchQuery.toLowerCase())) {
          acc.push(item);
        }
        // Children match
        else if (item.items) {
          const matchingChildren = item.items.filter((sub) =>
            sub.name.toLowerCase().includes(searchQuery.toLowerCase()),
          );
          matchingChildren.forEach((sub) =>
            acc.push({ ...sub, icon: item.icon }),
          );
        }
        return acc;
      }, [])
    : menu;

  const isEffectivelyCollapsed = isCollapsed;

  return (
    <>
      {/* Mobile Menu Toggle Button */}
      <button
        onClick={onToggleCollapse}
        className={`md:hidden fixed top-3 left-4 z-60 p-2 bg-white rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 shadow-sm transition-all ${
          !isCollapsed ? "opacity-0 pointer-events-none" : "opacity-100"
        }`}
      >
        <Menu size={20} />
      </button>

      {/* Mobile Overlay */}
      <AnimatePresence>
        {!isCollapsed && isMobile && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onToggleCollapse}
            className="md:hidden fixed inset-0 bg-black/20 z-40 backdrop-blur-sm"
          />
        )}
      </AnimatePresence>

      <motion.aside
        initial={false}
        animate={{ width: isMobile ? 280 : isEffectivelyCollapsed ? 80 : 256 }}
        transition={{
          duration: 0.4,
          type: "spring",
          stiffness: 90,
          damping: 20,
        }}
        onMouseEnter={() => {
          if (!isMobile && isCollapsed) setIsHovering(true);
        }}
        onMouseLeave={() => {
          if (!isMobile && isCollapsed) setIsHovering(false);
        }}
        className={`fixed left-0 top-0 h-screen bg-white/95 backdrop-blur-xl border-r border-slate-200 shadow-2xl z-50 overflow-visible flex flex-col transition-transform duration-300 md:translate-x-0 max-md:w-70! ${
          isCollapsed ? "max-md:-translate-x-full" : "max-md:translate-x-0"
        }`}
      >
        {/* ================= HEADER ================= */}
        <div
          className={`flex items-center h-20 shrink-0 transition-all duration-300 ${isEffectivelyCollapsed && !isMobile ? "justify-center px-0" : "justify-between px-6"}`}
        >
          <div
            className={`flex items-center gap-3 overflow-hidden cursor-pointer ${isEffectivelyCollapsed && !isMobile ? "w-full h-full justify-center group" : ""}`}
            title={isCollapsed && !isMobile ? "Expand Sidebar" : undefined}
          >
            <button
              type="button"
              onClick={() => {
                if (isCollapsed && !isMobile) {
                  onToggleCollapse();
                }
              }}
              className="w-10 h-10 bg-linear-to-br from-violet-600 to-purple-600 rounded-xl flex items-center justify-center shrink-0 shadow-lg shadow-violet-600/30 group-hover:scale-105 transition-transform duration-200"
            >
              {isEffectivelyCollapsed && !isMobile ? (
                <Menu className="w-5 h-5 text-white" />
              ) : (
                <Rocket className="w-5 h-5 text-white" />
              )}
            </button>
            <AnimatePresence>
              {(!isEffectivelyCollapsed || isMobile) && (
                <motion.div
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: "auto" }}
                  exit={{ opacity: 0, width: 0 }}
                  className="flex flex-col overflow-hidden"
                >
                  <span className="text-lg font-bold text-slate-900 leading-none tracking-tight flex flex-col gap-0.5">
                    <span>Sales</span>
                    <span className="text-violet-600">Automation</span>
                  </span>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {(!isEffectivelyCollapsed || isMobile) && (
            <button
              onClick={onToggleCollapse}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-all"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* ================= SEARCH ================= */}
        <div
          className={`px-4 mb-2 transition-all duration-300 ${isEffectivelyCollapsed && !isMobile ? "flex justify-center" : ""}`}
        >
          {isEffectivelyCollapsed && !isMobile ? (
            <button
              onClick={onToggleCollapse}
              className="p-2.5 rounded-xl hover:bg-slate-100 text-slate-500 transition-colors mx-auto block"
            >
              <Search className="w-5 h-5" />
            </button>
          ) : (
            <div className="relative group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
              <input
                type="text"
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all placeholder:text-slate-400 shadow-xs"
              />
            </div>
          )}
        </div>

        {/* ================= NAVIGATION ================= */}
        <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto overflow-x-visible scrollbar-thin scrollbar-thumb-slate-200 hover:scrollbar-thumb-slate-300">
          {displayMenu.length > 0
            ? displayMenu.map((item) => {
                const isParent = !!item.items;
                const count = 0;

                return (
                  <SidebarItem
                    key={item.name}
                    item={item}
                    count={count}
                    isCollapsed={isEffectivelyCollapsed && !isMobile}
                    isPermanentlyCollapsed={isCollapsed && !isMobile}
                    pathname={pathname}
                    hoveredItem={hoveredItem}
                    setHoveredItem={setHoveredItem}
                    onClick={handleNavigation}
                    onToggleCollapse={onToggleCollapse}
                  />
                );
              })
            : (!isEffectivelyCollapsed || isMobile) && (
                <div className="px-4 py-8 text-center">
                  <p className="text-sm text-slate-500">No modules found</p>
                </div>
              )}
        </nav>
      </motion.aside>
    </>
  );
}
