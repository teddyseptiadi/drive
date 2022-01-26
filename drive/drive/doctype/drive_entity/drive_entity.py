# Copyright (c) 2021, mituldavid and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet
from pathlib import Path
import shutil
from drive.utils.files import get_user_directory

class DriveEntity(NestedSet):
	nsm_parent_field = 'parent_drive_entity'
	def on_update(self):
		super().on_update()


	def before_save(self):
		self.version = self.version + 1


	def on_trash(self):
		if self.is_group:
			for child in self.get_children():
				child.delete()
		super().on_trash(True)


	def after_delete(self):
		"""Remove file once document is deleted"""
		if self.path:
			path = Path(self.path)
			path.unlink()


	def on_rollback(self):
		if self.flags.file_created:
			shutil.rmtree(self.path) if self.is_group else self.path.unlink()


	def move(self, new_parent=None):
		"""
		Move file or folder to the new parent folder

		:param new_parent: Document-name of the new parent folder. Defaults to the user directory
		:raises NotADirectoryError: If the new_parent is not a folder, or does not exist
		:raises FileExistsError: If a file or folder with the same name already exists in the specified parent folder
		:return: DriveEntity doc once file is moved
		"""

		new_parent = new_parent or get_user_directory().name
		is_group = frappe.db.get_value('Drive Entity', new_parent, 'is_group')
		if not is_group:
			raise NotADirectoryError()
		entity_exists = frappe.db.exists({
			'doctype': 'Drive Entity',
			'parent_drive_entity': new_parent,
			'title': self.title
		})
		if entity_exists:
			raise FileExistsError()
		self.parent_drive_entity = new_parent
		self.save()
		return self


	def rename(self, new_title):
		"""
		Rename file or folder

		:param new_title: New file or folder name
		:raises FileExistsError: If a file or folder with the same name already exists in the parent folder
		:return: DriveEntity doc once it's renamed
		"""

		entity_exists = frappe.db.exists({
			'doctype': 'Drive Entity',
			'parent_drive_entity': self.parent_drive_entity,
			'title': new_title
		})
		if entity_exists:
			raise FileExistsError()

		self.title = new_title
		self.save()
		return self


	def share(self, user, write=0, share=0, everyone=0, notify=1):
		if self.is_group:
			for child in self.get_children():
				child.share(user, write, share, everyone, 0)
			frappe.share.add('Drive Entity', self.name, user, write=write, share=share, everyone=everyone, notify=notify)
		else:
			frappe.share.add('Drive Entity', self.name, user, write=write, share=share, everyone=everyone, notify=notify)


	def unshare(self, user):
		if self.is_group:
			for child in self.get_children():
				child.unshare(user)
			frappe.share.remove('Drive Entity', self.name, user)
		else:
			frappe.share.remove('Drive Entity', self.name, user)