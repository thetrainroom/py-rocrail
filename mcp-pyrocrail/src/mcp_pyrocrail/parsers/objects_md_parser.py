"""Parser for OBJECTS.md documentation file"""

import re
from pathlib import Path
from typing import Any


class ObjectInfo:
    """Information about a PyRocrail object type"""

    def __init__(self, name: str):
        self.name = name
        self.element = ""
        self.description = ""
        self.file_path = ""
        self.official_docs: list[str] = []
        self.methods: dict[str, dict[str, Any]] = {}
        self.attributes: dict[str, str] = {}
        self.examples = ""


class ObjectsMdParser:
    """Parse OBJECTS.md file to extract API documentation"""

    def __init__(self, objects_md_path: str):
        self.path = Path(objects_md_path)
        self.objects: dict[str, ObjectInfo] = {}
        self.aliases: dict[str, str] = {}  # Map element tags to object names
        self._parse()

    def _parse(self) -> None:
        """Parse the OBJECTS.md file"""
        content = self.path.read_text(encoding="utf-8")

        # Split by ## headers (each object section)
        sections = re.split(r'\n## ', content)

        for section in sections[1:]:  # Skip intro
            self._parse_object_section(section)

    def _parse_object_section(self, section: str) -> None:
        """Parse a single object section"""
        lines = section.split('\n')
        if not lines:
            return

        # Get object name from first line
        obj_name = lines[0].strip()

        # Skip non-object sections
        if obj_name in ['Quick Reference', 'Additional Resources']:
            return

        obj = ObjectInfo(obj_name)

        # Extract element tag and file path (can be on same line or separate)
        for line in lines[1:10]:  # Check first few lines
            if '**Element**:' in line:
                # Extract element tag
                match = re.search(r'`<(\w+)>`', line)
                if match:
                    obj.element = match.group(1)
                # Check for file path on same line
                if '**File**:' in line:
                    match = re.search(r'\*\*File\*\*:\s*`([^`]+)`', line)
                    if match:
                        obj.file_path = match.group(1)
            elif line.startswith('**File**:'):
                match = re.search(r'`([^`]+)`', line)
                if match:
                    obj.file_path = match.group(1)
            elif line.startswith('**Description**:'):
                obj.description = line.replace('**Description**:', '').strip()

        # Extract official documentation links
        for line in lines:
            if line.startswith('- [') and 'wiki.rocrail.net' in line:
                match = re.search(r'\((https://[^)]+)\)', line)
                if match:
                    obj.official_docs.append(match.group(1))

        # Extract methods
        in_methods = False
        in_code_block = False
        current_method = None
        method_desc = []

        i = 0
        while i < len(lines):
            line = lines[i]

            if line.startswith('### Methods'):
                in_methods = True
                i += 1
                continue
            elif line.startswith('### ') and not line.startswith('#### '):
                # Only ### headers (not ####) end the methods section
                in_methods = False
                i += 1
                continue

            if in_methods:
                # Check for start of code block
                if line.strip() == '```python':
                    in_code_block = True
                    i += 1
                    # Next line should be the method signature
                    if i < len(lines):
                        sig_line = lines[i]
                        # Match: object.method(params) -> return_type
                        match = re.match(r'(\w+)\.(\w+)\((.*?)\)\s*(?:->|→)\s*(.+)', sig_line.strip())
                        if match:
                            method_name = match.group(2)
                            params = match.group(3).strip()
                            return_type = match.group(4).strip()
                            current_method = method_name
                            obj.methods[method_name] = {
                                'params': params,
                                'return_type': return_type,
                                'description': '',
                                'command': ''
                            }
                            method_desc = []
                    i += 1
                    continue

                # Check for end of code block
                elif line.strip() == '```':
                    in_code_block = False
                    i += 1
                    # After code block, collect description lines
                    while i < len(lines):
                        desc_line = lines[i]
                        # Stop at next code block or empty line followed by code block
                        if desc_line.strip() == '```python' or desc_line.startswith('####') or desc_line.startswith('###'):
                            break
                        if desc_line.strip() == '':
                            i += 1
                            continue
                        if current_method:
                            if 'cmd=' in desc_line:
                                obj.methods[current_method]['command'] = desc_line.strip()
                            else:
                                method_desc.append(desc_line.strip())
                                obj.methods[current_method]['description'] = ' '.join(method_desc)
                        i += 1
                    continue

            i += 1

        # Extract attributes
        in_attributes = False
        for i, line in enumerate(lines):
            if line.startswith('### Key Attributes'):
                in_attributes = True
                continue
            elif line.startswith('###'):
                in_attributes = False

            if in_attributes and line.startswith('- `'):
                match = re.match(r'- `(\w+)`: (.+)', line)
                if match:
                    attr_name = match.group(1)
                    attr_desc = match.group(2)
                    obj.attributes[attr_name] = attr_desc

        # Extract example section
        in_example = False
        example_lines = []
        for line in lines:
            if line.startswith('### Example Usage'):
                in_example = True
                continue
            elif line.startswith('###') or line.startswith('---'):
                in_example = False

            if in_example:
                example_lines.append(line)

        obj.examples = '\n'.join(example_lines).strip()

        # Store object
        self.objects[obj_name] = obj
        if obj.element:
            self.aliases[obj.element] = obj_name
            # Add common variations
            self.aliases[obj_name.lower()] = obj_name

    def get_object(self, name: str) -> ObjectInfo | None:
        """Get object by name or element tag"""
        # Direct match
        if name in self.objects:
            return self.objects[name]
        # Alias match (element tag or lowercase)
        if name in self.aliases:
            return self.objects[self.aliases[name]]
        # Case-insensitive match
        for obj_name in self.objects:
            if obj_name.lower() == name.lower():
                return self.objects[obj_name]
        return None

    def list_all_objects(self) -> list[str]:
        """List all object names"""
        return list(self.objects.keys())

    def search_methods(self, query: str) -> list[tuple[str, str, dict[str, Any]]]:
        """Search for methods matching query"""
        results = []
        query_lower = query.lower()
        for obj_name, obj in self.objects.items():
            for method_name, method_info in obj.methods.items():
                if (query_lower in method_name.lower() or
                    query_lower in method_info.get('description', '').lower()):
                    results.append((obj_name, method_name, method_info))
        return results
