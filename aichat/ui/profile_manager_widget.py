"""
Profile manager widget for managing AI profiles.
"""
from typing import Optional, Callable, Dict, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QMessageBox, QMenu, QInputDialog, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont

from ..profiles.manager import ProfileManager
from ..profiles.models import Profile
from .profile_dialog import ProfileDialog
from .model_dialog import ModelDialog

class ProfileManagerWidget(QWidget):
    """
    A widget for managing AI profiles.
    """
    
    profile_selected = pyqtSignal(Profile)
    
    def __init__(self, profile_manager: ProfileManager, parent=None):
        """
        Initialize the profile manager widget.
        
        Args:
            profile_manager: Profile manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.current_profile = None
        
        self.init_ui()
        self.refresh_profiles()
        
        # Select the default profile if available
        default_profile = self.profile_manager.get_default_profile()
        if default_profile:
            self.select_profile(default_profile.id)
    
    def init_ui(self) -> None:
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        
        # Title
        title_layout = QHBoxLayout()
        title_label = QLabel("AI Profiles")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Add profile button
        self.add_btn = QPushButton("Add Profile")
        self.add_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_FileDialogNewFolder', 'SP_FileIcon')))
        self.add_btn.clicked.connect(self.add_profile)
        title_layout.addWidget(self.add_btn)
        
        layout.addLayout(title_layout)
        
        # Profile list
        self.profile_list = QListWidget()
        self.profile_list.setIconSize(QSize(32, 32))
        self.profile_list.itemSelectionChanged.connect(self.on_profile_selected)
        self.profile_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.profile_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.profile_list)
        
        # Profile actions
        btn_layout = QHBoxLayout()
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self.edit_selected_profile)
        btn_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_selected_profile)
        btn_layout.addWidget(self.delete_btn)
        
        self.set_default_btn = QPushButton("Set as Default")
        self.set_default_btn.setEnabled(False)
        self.set_default_btn.clicked.connect(self.set_default_profile)
        btn_layout.addWidget(self.set_default_btn)
        
        layout.addLayout(btn_layout)
        
        # Import/Export buttons
        io_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("Import")
        self.import_btn.clicked.connect(self.import_profile)
        io_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_profile)
        io_layout.addWidget(self.export_btn)
        
        layout.addLayout(io_layout)
    
    def refresh_profiles(self) -> None:
        """Refresh the list of profiles."""
        self.profile_list.clear()
        profiles = self.profile_manager.list_profiles()
        
        for profile in profiles:
            item = QListWidgetItem(profile.name)
            item.setData(Qt.UserRole, profile.id)
            
            # Add icon based on profile type or default
            if profile.is_default:
                item.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_DialogApplyButton', 'SP_MessageBoxInformation')))
            
            # Add tooltip with more info
            tooltip = f"""
            <b>{profile.name}</b><br/>
            {profile.description}<br/>
            <br/>
            <i>ID:</i> {profile.id}<br/>
            <i>Version:</i> {profile.version}<br/>
            <i>Author:</i> {profile.author or 'N/A'}<br/>
            <i>Models:</i> {len(profile.models)}<br/>
            <i>Tools:</i> {', '.join(profile.tools_enabled) if profile.tools_enabled else 'None'}
            """
            item.setToolTip(tooltip.strip())
            
            self.profile_list.addItem(item)
    
    def get_selected_profile_id(self) -> Optional[str]:
        """
        Get the ID of the currently selected profile.
        
        Returns:
            Profile ID or None if no profile is selected
        """
        selected = self.profile_list.selectedItems()
        if not selected:
            return None
        return selected[0].data(Qt.UserRole)
    
    def select_profile(self, profile_id: str) -> bool:
        """
        Select a profile by ID.
        
        Args:
            profile_id: ID of the profile to select
            
        Returns:
            True if the profile was found and selected, False otherwise
        """
        for i in range(self.profile_list.count()):
            item = self.profile_list.item(i)
            if item.data(Qt.UserRole) == profile_id:
                self.profile_list.setCurrentItem(item)
                return True
        return False
    
    def on_profile_selected(self) -> None:
        """Handle profile selection change."""
        profile_id = self.get_selected_profile_id()
        
        # Update button states
        has_selection = profile_id is not None
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.export_btn.setEnabled(has_selection)
        self.set_default_btn.setEnabled(has_selection)
        
        # Emit signal if a profile is selected
        if has_selection:
            try:
                profile = self.profile_manager.get_profile(profile_id)
                self.current_profile = profile
                self.profile_selected.emit(profile)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load profile: {str(e)}")
    
    def show_context_menu(self, position) -> None:
        """Show the context menu for the profile list."""
        item = self.profile_list.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        
        edit_action = menu.addAction("Edit Profile")
        edit_action.triggered.connect(self.edit_selected_profile)
        
        delete_action = menu.addAction("Delete Profile")
        delete_action.triggered.connect(self.delete_selected_profile)
        
        menu.addSeparator()
        
        set_default_action = menu.addAction("Set as Default")
        set_default_action.triggered.connect(self.set_default_profile)
        
        menu.addSeparator()
        
        export_action = menu.addAction("Export Profile")
        export_action.triggered.connect(self.export_profile)
        
        menu.exec_(self.profile_list.viewport().mapToGlobal(position))
    
    def add_profile(self) -> None:
        """Add a new profile."""
        dialog = ProfileDialog(self.profile_manager, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_profiles()
            if dialog.profile:
                self.select_profile(dialog.profile.id)
    
    def edit_selected_profile(self) -> None:
        """Edit the selected profile."""
        profile_id = self.get_selected_profile_id()
        if not profile_id:
            return
            
        try:
            profile = self.profile_manager.get_profile(profile_id)
            dialog = ProfileDialog(self.profile_manager, profile, self)
            if dialog.exec_() == QDialog.Accepted:
                self.refresh_profiles()
                # Reselect the profile to update the UI
                self.select_profile(profile_id)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to edit profile: {str(e)}")
    
    def delete_selected_profile(self) -> None:
        """Delete the selected profile."""
        profile_id = self.get_selected_profile_id()
        if not profile_id:
            return
            
        try:
            profile = self.profile_manager.get_profile(profile_id)
            
            # Don't allow deleting the default profile
            if profile.is_default:
                QMessageBox.warning(
                    self,
                    "Cannot Delete",
                    "Cannot delete the default profile. Please set another profile as default first."
                )
                return
            
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete the profile '{profile.name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.profile_manager.delete_profile(profile_id)
                self.refresh_profiles()
                
                # Clear selection
                self.profile_list.clearSelection()
                self.current_profile = None
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to delete profile: {str(e)}")
    
    def set_default_profile(self) -> None:
        """Set the selected profile as the default."""
        profile_id = self.get_selected_profile_id()
        if not profile_id:
            return
            
        try:
            self.profile_manager.set_default_profile(profile_id)
            self.refresh_profiles()
            
            # Reselect the profile to update the UI
            self.select_profile(profile_id)
            
            QMessageBox.information(
                self,
                "Default Profile Set",
                f"The profile has been set as the default."
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to set default profile: {str(e)}")
    
    def import_profile(self) -> None:
        """Import a profile from a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Profile",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            # Show import options
            options = ["Import as New Profile", "Overwrite Existing Profile"]
            option, ok = QInputDialog.getItem(
                self,
                "Import Options",
                "How would you like to import the profile?",
                options,
                0,
                False
            )
            
            if not ok:
                return
                
            overwrite = (option == options[1])  # Overwrite if second option selected
            
            # Import the profile
            imported_profile = self.profile_manager.import_profile(file_path, overwrite=overwrite)
            
            # Refresh and select the imported profile
            self.refresh_profiles()
            self.select_profile(imported_profile.id)
            
            QMessageBox.information(
                self,
                "Import Successful",
                f"Successfully imported profile: {imported_profile.name}"
            )
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Import Failed",
                f"Failed to import profile: {str(e)}"
            )
    
    def export_profile(self) -> None:
        """Export the selected profile to a file."""
        profile_id = self.get_selected_profile_id()
        if not profile_id:
            return
            
        try:
            profile = self.profile_manager.get_profile(profile_id)
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Profile",
                f"{profile.name.lower().replace(' ', '_')}.json",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if file_path:
                # Ensure .json extension
                if not file_path.lower().endswith('.json'):
                    file_path += '.json'
                
                self.profile_manager.export_profile(profile_id, file_path)
                
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Successfully exported profile to:\n{file_path}"
                )
                
        except Exception as e:
            QMessageBox.warning(
                self,
                "Export Failed",
                f"Failed to export profile: {str(e)}"
            )
