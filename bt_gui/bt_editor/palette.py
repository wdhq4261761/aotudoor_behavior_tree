import customtkinter as ctk
from typing import List, Callable, Optional

from ..theme import Theme
from .constants import build_node_categories


NODE_CATEGORIES = build_node_categories(Theme.NODE_COLORS)


class NodeButton(ctk.CTkFrame):
    def __init__(self, master, node_type: str, display_name: str, description: str, 
                 color_config: dict, on_click: Callable[[str], None], **kwargs):
        super().__init__(master, **kwargs)
        self.node_type = node_type
        self.on_click = on_click
        self.color_config = color_config
        
        self._dark_colors = Theme.get_dark_colors()
        self.configure(
            fg_color=self._dark_colors['bg_tertiary'],
            corner_radius=Theme.DIMENSIONS['button_corner_radius'],
            cursor="hand2"
        )
        
        self._create_ui(display_name, description)
        self._bind_events()
    
    def _create_ui(self, display_name: str, description: str):
        self.color_indicator = ctk.CTkFrame(
            self,
            width=4,
            height=32,
            fg_color=self.color_config['bg'],
            corner_radius=2
        )
        self.color_indicator.pack(side="left", fill="y", padx=(4, 8), pady=4)
        
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(side="left", fill="both", expand=True, pady=4)
        
        self.name_label = ctk.CTkLabel(
            content_frame,
            text=display_name,
            font=Theme.get_font('sm'),
            text_color=self._dark_colors['text_primary'],
            anchor="w"
        )
        self.name_label.pack(fill="x")
        
        self.desc_label = ctk.CTkLabel(
            content_frame,
            text=description,
            font=Theme.get_font('xs'),
            text_color=self._dark_colors['text_muted'],
            anchor="w"
        )
        self.desc_label.pack(fill="x")
    
    def _bind_events(self):
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.name_label.bind("<Button-1>", self._on_click)
        self.desc_label.bind("<Button-1>", self._on_click)
    
    def _on_enter(self, event):
        self.configure(fg_color=self._dark_colors['border'])
    
    def _on_leave(self, event):
        self.configure(fg_color=self._dark_colors['bg_tertiary'])
    
    def _on_click(self, event):
        if self.on_click:
            self.on_click(self.node_type)


class CategorySection(ctk.CTkFrame):
    def __init__(self, master, category_name: str, category_data: dict,
                 on_node_click: Callable[[str], None], **kwargs):
        super().__init__(master, **kwargs)
        self.category_name = category_name
        self.category_data = category_data
        self.on_node_click = on_node_click
        self._is_expanded = True
        
        self._dark_colors = Theme.get_dark_colors()
        self.configure(fg_color="transparent")
        
        self._create_ui()
    
    def _create_ui(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent", cursor="hand2")
        self.header.pack(fill="x")
        self.header.bind("<Button-1>", self._toggle_expand)
        
        self.expand_icon = ctk.CTkLabel(
            self.header,
            text="▼" if self._is_expanded else "▶",
            font=Theme.get_font('xs'),
            text_color=self._dark_colors['text_muted'],
            width=16
        )
        self.expand_icon.pack(side="left")
        self.expand_icon.bind("<Button-1>", self._toggle_expand)
        
        color_config = self.category_data['color']
        self.category_indicator = ctk.CTkFrame(
            self.header,
            width=12,
            height=12,
            fg_color=color_config['bg'],
            corner_radius=3
        )
        self.category_indicator.pack(side="left", padx=(4, 8))
        self.category_indicator.bind("<Button-1>", self._toggle_expand)
        
        self.category_label = ctk.CTkLabel(
            self.header,
            text=self.category_name,
            font=Theme.get_font('sm'),
            text_color=self._dark_colors['text_primary']
        )
        self.category_label.pack(side="left")
        self.category_label.bind("<Button-1>", self._toggle_expand)
        
        self.nodes_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nodes_frame.pack(fill="x", pady=(Theme.DIMENSIONS['spacing_xs'], 0))
        
        for node_type, display_name, description in self.category_data['nodes']:
            btn = NodeButton(
                self.nodes_frame,
                node_type=node_type,
                display_name=display_name,
                description=description,
                color_config=color_config,
                on_click=self.on_node_click
            )
            btn.pack(fill="x", pady=Theme.DIMENSIONS['spacing_xs'])
    
    def _toggle_expand(self, event=None):
        self._is_expanded = not self._is_expanded
        self.expand_icon.configure(text="▼" if self._is_expanded else "▶")
        
        if self._is_expanded:
            self.nodes_frame.pack(fill="x", pady=(Theme.DIMENSIONS['spacing_xs'], 0))
        else:
            self.nodes_frame.pack_forget()


class NodePalette(ctk.CTkFrame):
    def __init__(self, master, on_node_add: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_node_add = on_node_add
        
        self._dark_colors = Theme.get_dark_colors()
        self.configure(
            fg_color=self._dark_colors['sidebar_bg'],
            corner_radius=0,
            width=Theme.DIMENSIONS['sidebar_width']
        )
        
        self._create_ui()
    
    def _create_ui(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=Theme.DIMENSIONS['spacing_md'], pady=Theme.DIMENSIONS['spacing_md'])
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="节点面板",
            font=Theme.get_font('lg'),
            text_color=self._dark_colors['text_primary']
        )
        title_label.pack(side="left")
        
        search_frame = ctk.CTkFrame(self, fg_color=self._dark_colors['bg_tertiary'], corner_radius=6)
        search_frame.pack(fill="x", padx=Theme.DIMENSIONS['spacing_md'], pady=(0, Theme.DIMENSIONS['spacing_md']))
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="搜索节点...",
            font=Theme.get_font('sm'),
            height=Theme.DIMENSIONS['input_height'],
            fg_color="transparent",
            border_width=0,
            text_color=self._dark_colors['text_primary'],
            placeholder_text_color=self._dark_colors['text_muted']
        )
        self.search_entry.pack(fill="x", padx=Theme.DIMENSIONS['spacing_sm'], pady=Theme.DIMENSIONS['spacing_xs'])
        self.search_entry.bind("<KeyRelease>", self._on_search)
        
        self.content_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self._dark_colors['bg_tertiary'],
            scrollbar_button_hover_color=self._dark_colors['border']
        )
        self.content_frame.pack(fill="both", expand=True, padx=Theme.DIMENSIONS['spacing_md'])
        
        self.category_sections: List[CategorySection] = []
        for category_name, category_data in NODE_CATEGORIES.items():
            section = CategorySection(
                self.content_frame,
                category_name=category_name,
                category_data=category_data,
                on_node_click=self._on_node_click
            )
            section.pack(fill="x", pady=(0, Theme.DIMENSIONS['spacing_md']))
            self.category_sections.append(section)
    
    def _on_search(self, event):
        search_text = self.search_entry.get().lower()
        
        for section in self.category_sections:
            has_match = False
            
            for child in section.nodes_frame.winfo_children():
                if isinstance(child, NodeButton):
                    node_data = section.category_data['nodes']
                    node_info = next((n for n in node_data if n[0] == child.node_type), None)
                    
                    if node_info:
                        display_name = node_info[1].lower()
                        description = node_info[2].lower()
                        
                        if search_text in display_name or search_text in description or search_text == "":
                            child.pack(fill="x", pady=Theme.DIMENSIONS['spacing_xs'])
                            has_match = True
                        else:
                            child.pack_forget()
            
            if search_text == "":
                section.pack(fill="x", pady=(0, Theme.DIMENSIONS['spacing_md']))
            elif has_match:
                section.pack(fill="x", pady=(0, Theme.DIMENSIONS['spacing_md']))
                if not section._is_expanded:
                    section._toggle_expand()
            else:
                section.pack_forget()
    
    def _on_node_click(self, node_type: str):
        if self.on_node_add:
            self.on_node_add(node_type)
