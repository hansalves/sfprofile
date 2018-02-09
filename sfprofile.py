#!/usr/bin/env python3
#
# MIT License
#
# Copyright (c) 2018 Hans Alves
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import argparse
import os
import os.path
import glob
import sys
import re
import fnmatch
import xml.etree.ElementTree as ET

namespace = "http://soap.sforce.com/2006/04/metadata"
namespaceb = '{' + namespace + '}'
namespacelen = len(namespaceb)
namespacedict = {"xmlns": namespace}

def debug(*argl, **argd):
	print(*argl, **argd, file=sys.stderr)

def nodeToDict(node):
	return dict((c.tag[namespacelen:], c.text) for c in  list(node))

def checkdir():
	if 'profiles' not in os.listdir():
		print('No profiles or profile folder found.', file=sys.stderr)
		return False
	return True

def getChildNode(node, nodeName):
	children = node.findall('xmlns:' + nodeName, namespacedict)
	if len(children) == 0:
		print('Error: Missing {} child in {} node.'.format(nodeName, node.tag[namespacelen:]), file=sys.stderr)
		sys.exit(1)
	elif len(children) > 1:
		print('Error: Too many {} children in {} node.'.format(nodeName, node.tag[namespacelen:]), file=sys.stderr)
		sys.exit(1)
	return children[0]

class SFProfile:
	def __init__(self, filename):
		self.filename = filename
		m = re.match(r'^profiles[/\\](.*).profile$', filename)
		self.name = m.group(1)
		self.tree = ET.parse(filename)
		self.root = self.tree.getroot()

	def getAllNodesOfType(self, typename):
		for node in self.root.findall('xmlns:' + typename, namespacedict):
			yield node

	def getFieldPermissions(self):
		return self.getAllNodesOfType('fieldPermissions')

	def getObjectPermissions(self):
		return self.getAllNodesOfType('objectPermissions')

	def allowAllOnObject(self, objectName):
		for node in self.getObjectPermissions():
			if getChildNode(node, 'object').text == objectName:
				#~ debug(nodeToDict(node))
				getChildNode(node, 'allowRead').text = 'true'
				getChildNode(node, 'allowCreate').text = 'true'
				getChildNode(node, 'allowEdit').text = 'true'
				getChildNode(node, 'allowDelete').text = 'true'
				getChildNode(node, 'viewAllRecords').text = 'true'
				getChildNode(node, 'modifyAllRecords').text = 'true'

		objectName = objectName + '.'
		for node in self.getFieldPermissions():
			if getChildNode(node, 'field').text.find(objectName) == 0:
				#~ debug(nodeToDict(node))
				getChildNode(node, 'readable').text = 'true'
				getChildNode(node, 'editable').text = 'true'

	def setObjectPermission(self, objectName, read, create, edit, delete, viewall, modifyall):
		found = False
		for node in self.getObjectPermissions():
			if getChildNode(node, 'object').text == objectName:
				found = True
				#~ debug(nodeToDict(node))
				getChildNode(node, 'allowRead').text = read
				getChildNode(node, 'allowCreate').text = create
				getChildNode(node, 'allowEdit').text = edit
				getChildNode(node, 'allowDelete').text = delete
				getChildNode(node, 'viewAllRecords').text = viewall
				getChildNode(node, 'modifyAllRecords').text = modifyall
		if not found:
			# add new node
			tag = namespaceb + 'objectPermissions'
			objectPermissions = ET.Element(tag)
			obj = ET.SubElement(objectPermissions, namespaceb + 'object')
			obj.text = objectName
			allowRead = ET.SubElement(objectPermissions, namespaceb + 'allowRead')
			allowRead.text = read;
			allowCreate = ET.SubElement(objectPermissions, namespaceb + 'allowCreate')
			allowCreate.text = read;
			allowEdit = ET.SubElement(objectPermissions, namespaceb + 'allowEdit')
			allowEdit.text = read;
			allowDelete = ET.SubElement(objectPermissions, namespaceb + 'allowDelete')
			allowDelete.text = read;
			viewAllRecords = ET.SubElement(objectPermissions, namespaceb + 'viewAllRecords')
			viewAllRecords.text = read;
			modifyAllRecords = ET.SubElement(objectPermissions, namespaceb + 'modifyAllRecords')
			modifyAllRecords.text = read;
			idx = 0
			for node in list(self.root):
				if node.tag > tag:
					break
				idx += 1
			self.root.insert(idx, objectPermissions)

	def setFieldPermission(self, fieldName, read, edit):
		found = False
		for node in self.getFieldPermissions():
			if getChildNode(node, 'field').text == fieldName:
				found = True
				#~ debug(nodeToDict(node))
				getChildNode(node, 'readable').text = read
				getChildNode(node, 'editable').text = edit
		if not found:
			# add new node
			tag = namespaceb + 'fieldPermissions'
			fieldPermissions = ET.Element(tag)
			field = ET.SubElement(fieldPermissions, namespaceb + 'field')
			field.text = fieldName
			readable = ET.SubElement(fieldPermissions, namespaceb + 'readable')
			readable.text = read
			editable = ET.SubElement(fieldPermissions, namespaceb + 'editable')
			editable.text = edit
			idx = 0
			for node in list(self.root):
				if node.tag > namespaceb + 'fieldPermissions':
					break
				idx += 1
			self.root.insert(idx, fieldPermissions)

	def removeTag(self, typename, identitytag, ident):
		exp = re.compile(fnmatch.translate(ident))
		for node in self.root.findall('xmlns:' + typename, namespacedict):
			if (identitytag == '*' or
				exp.match(getChildNode(node, identitytag).text)
				):
				self.root.remove(node)

	def removeMissing(self, objects, fields, recordtypes):
		objecttag = '{' + namespace + '}object'
		fieldtag = '{' + namespace + '}field'
		recordtypetag = '{' + namespace + '}recordType'
		for node in list(self.root):
			for node2 in list(node):
				if ((node2.tag == objecttag and node2.text not in objects) or
					(node2.tag == fieldtag and (node2.text not in fields or node2.text.split('.')[0] not in objects)) or
					(node2.tag == recordtypetag and (node2.text not in recordtypes or node2.text.split('.')[0] not in objects))
					):
					#~ debug('removing missing', node2.tag, node2.text)
					self.root.remove(node)
					break
				# TODO Tabs, Pages, Classes

	def removeRequiredFields(self, fields):
		fieldtag = '{' + namespace + '}field'
		for node in list(self.root):
			for node2 in list(node):
				if node2.tag == fieldtag and node2.text in fields:
					#~ debug('removing required', node2.tag, node2.text)
					self.root.remove(node)
					break

	def write(self, inPlace):
		if inPlace:
			print('Writing', self.filename, file=sys.stderr)
			f = open(self.filename, 'w')
		else:
			print('Writing', self.filename + '.new', file=sys.stderr)
			f = open(self.filename + '.new', 'w')
		self.tree.write(f, encoding="unicode", xml_declaration=True, default_namespace=namespace)

	def __repr__(self):
		return "{Profile '" + self.name + "'}"

class SFObject:
	def __init__(self, filename):
		self.filename = filename
		m = re.match(r'^objects[/\\](.*).object$', filename)
		self.name = m.group(1)
		tree = ET.parse(filename)
		root = tree.getroot()
		self.fields = set()
		self.requiredFields = set()
		for node in root.findall('xmlns:fields', namespacedict):
			self.fields.add(getChildNode(node, 'fullName').text)
			for requiredNode in node.findall('xmlns:type', namespacedict):
				if requiredNode.text == 'MasterDetail':
					self.requiredFields.add(getChildNode(node, 'fullName').text)
			for requiredNode in node.findall('xmlns:required', namespacedict):
				if requiredNode.text == 'true':
					self.requiredFields.add(getChildNode(node, 'fullName').text)
		self.recordTypes = []
		for node in root.findall('xmlns:recordTypes', namespacedict):
			self.recordTypes.append(getChildNode(node, 'fullName').text)

def main():
	parser = argparse.ArgumentParser(description='Field level security setter for Salesforce profiles')
	parser.add_argument('-p', '--profile', dest='profiles', action='append',
		metavar='PROFILE', default=[],
		help='Operate only on PROFILE.')
	parser.add_argument('-a', '--allow-all-on-object', dest='allowObjects', action='append',
		metavar='ALLOWOBJECT', default=[],
		help='Allow all operations on ALLOWOBJECT.')
	parser.add_argument('-o', '--set-object-permission', dest='objectPermissions', action='append',
		metavar=('OBJECT', 'READ', 'CREATE', 'EDIT', 'DELETE', 'VIEWALL', 'MODIFYALL'), default=[], nargs=7,
		help='set permissions on OBJECT.')
	parser.add_argument('-f', '--set-field-permission', dest='fieldPermissions', action='append',
		metavar=('FIELDNAME', 'READABLE', 'EDITABLE'), default=[], nargs=3,
		help='Set field level security for FIELDNAME.')
	parser.add_argument('-r', '--remove-tag', dest='removeTags', action='append', nargs=3,
		metavar=('TYPE', 'IDENTITYTAG',  'IDENTITY'), default=[],
		help='Remove tags of TYPE with IDENTITYTAG value IDENTITY')
	parser.add_argument('-m', '--remove-missing-objects', dest='removeMissing', action='store_true', default=False,
		help='Remove tags for objects, fields and record types that are not found in the objects directory')
	parser.add_argument('-R', '--remove-required-fields', dest='removeRequired', action='store_true', default=False,
		help='Remove tags required fields that are found in the objects directory')
	parser.add_argument('-i', '--in-place', dest='inPlace', action='store_true', default=False,
		help='Edit the profile files in place')
	args = parser.parse_args()

	if not checkdir():
		return


	if not args.profiles:
		profiles = [SFProfile(f) for f in glob.glob(os.path.join('profiles', '*.profile'))]
	else:
		profiles = []

	for prof in args.profiles:
		filename = os.path.join('profiles', prof + '.profile')
		if os.path.isfile(filename):
			profiles.append(SFProfile(filename))
		else:
			print('Profile', prof, 'not found.', file=sys.stderr)
			return

	for fps in args.fieldPermissions:
		if not re.match('^\w+\.\w+$', fps[0]):
			print(fps[0], 'is not a valid field name.', file=sys.stderr)
			return
		i = 1
		for f in ('READABLE', 'EDITABLE'):
			if fps[i] not in ('true', 'false'):
				print(f, 'should be true or false.', file=sys.stderr)
				return
			i += 1
	for obj in args.objectPermissions:
		i = 1
		for f in ('READ', 'CREATE', 'EDIT', 'DELETE', 'VIEWALL', 'MODIFYALL'):
			if obj[i] not in ('true', 'false'):
				print(f, 'should be true or false.', file=sys.stderr)
				return
			i += 1

	if args.removeMissing or args.removeRequired:
		objectsDict = {}
		fieldsSet = set()
		recordTypesSet = set()
		requiredFieldsSet = set()
		for filename in glob.glob(os.path.join('objects', '*.object')):
			obj = SFObject(filename)
			objectsDict[obj.name] = obj
			for fieldname in obj.fields:
				fieldsSet.add(obj.name + '.' + fieldname)
			for typename in obj.recordTypes:
				recordTypesSet.add(obj.name + '.' + typename)
			for fieldname in obj.requiredFields:
				requiredFieldsSet.add(obj.name + '.' + fieldname)

	for prof in profiles:
		for obj in args.allowObjects:
			prof.allowAllOnObject(obj)
		for rmtag in args.removeTags:
			prof.removeTag(rmtag[0], rmtag[1], rmtag[2])
		for fps in args.fieldPermissions:
			prof.setFieldPermission(fps[0], fps[1], fps[2])
		for obj in args.objectPermissions:
			prof.setObjectPermission(obj[0], obj[1], obj[2], obj[3], obj[4], obj[5], obj[6])
		if args.removeMissing:
			prof.removeMissing(objectsDict, fieldsSet, recordTypesSet)
		if args.removeRequired:
			prof.removeRequiredFields(requiredFieldsSet)
		prof.write(args.inPlace)

if __name__ == '__main__':
	main()
