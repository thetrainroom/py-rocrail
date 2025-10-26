"""Documentation lookup tools"""


from ..parsers.objects_md_parser import ObjectsMdParser, ObjectInfo


class DocsLookup:
    """Lookup PyRocrail API documentation"""

    def __init__(self, objects_md_path: str):
        self.parser = ObjectsMdParser(objects_md_path)

    def api_lookup(self, object_type: str, method: str | None = None) -> str:
        """
        Get API documentation for an object type or specific method

        Args:
            object_type: Object type name (e.g., "locomotive", "lc", "switch")
            method: Optional method name to get specific documentation

        Returns:
            Formatted documentation string
        """
        obj = self.parser.get_object(object_type)
        if not obj:
            return self._object_not_found(object_type)

        if method:
            return self._format_method(obj, method)
        else:
            return self._format_object_overview(obj)

    def list_methods(self, object_type: str) -> str:
        """
        List all methods available for an object type

        Args:
            object_type: Object type name

        Returns:
            Formatted list of methods with brief descriptions
        """
        obj = self.parser.get_object(object_type)
        if not obj:
            return self._object_not_found(object_type)

        if not obj.methods:
            return f"{obj.name} has no methods documented."

        lines = [f"{obj.name} methods:\n"]
        for method_name, method_info in obj.methods.items():
            desc = method_info.get('description', '').split('.')[0]  # First sentence
            params = method_info.get('params', '')
            lines.append(f"- {method_name}({params}) - {desc}")

        return '\n'.join(lines)

    def get_attributes(self, object_type: str) -> str:
        """
        Get all attributes for an object type

        Args:
            object_type: Object type name

        Returns:
            Formatted list of attributes with descriptions
        """
        obj = self.parser.get_object(object_type)
        if not obj:
            return self._object_not_found(object_type)

        if not obj.attributes:
            return f"{obj.name} has no attributes documented."

        lines = [f"{obj.name} attributes:\n"]
        for attr_name, attr_desc in obj.attributes.items():
            lines.append(f"- {attr_name}: {attr_desc}")

        lines.append(f"\nSee: OBJECTS.md#{obj.name.lower()} for full details")
        return '\n'.join(lines)

    def check_method(self, object_type: str, method: str) -> str:
        """
        Check if a method exists and validate it

        Args:
            object_type: Object type name
            method: Method name to check

        Returns:
            Validation result with suggestions if method doesn't exist
        """
        obj = self.parser.get_object(object_type)
        if not obj:
            return self._object_not_found(object_type)

        if method in obj.methods:
            method_info = obj.methods[method]
            params = method_info.get('params', '')
            return_type = method_info.get('return_type', 'None')
            desc = method_info.get('description', '')
            return f"✅ Method '{method}' exists for {obj.name}\n\nSignature: {method}({params}) -> {return_type}\n\n{desc}"

        # Method doesn't exist - suggest alternatives
        suggestions = self._find_similar_methods(obj, method)
        result = f"❌ Method '{method}' does not exist for {obj.name}\n"

        if suggestions:
            result += "\nDid you mean:\n"
            for suggestion in suggestions[:3]:  # Top 3 suggestions
                method_info = obj.methods[suggestion]
                desc = method_info.get('description', '').split('.')[0]
                result += f"- {suggestion}() - {desc}\n"
        elif obj.methods:
            # No similar methods, but show some available methods
            result += "\nDid you mean:\n"
            for method_name in list(obj.methods.keys())[:3]:
                method_info = obj.methods[method_name]
                desc = method_info.get('description', '').split('.')[0]
                result += f"- {method_name}() - {desc}\n"

        return result

    def search(self, query: str) -> str:
        """
        Search across all documentation

        Args:
            query: Search term

        Returns:
            Formatted search results
        """
        results = self.parser.search_methods(query)

        if not results:
            return f"No results found for '{query}'"

        lines = [f"Search results for '{query}':\n"]
        for obj_name, method_name, method_info in results[:10]:  # Top 10 results
            desc = method_info.get('description', '').split('.')[0]
            lines.append(f"- {obj_name}.{method_name}() - {desc}")

        if len(results) > 10:
            lines.append(f"\n... and {len(results) - 10} more results")

        return '\n'.join(lines)

    def _format_object_overview(self, obj: ObjectInfo) -> str:
        """Format complete object overview"""
        lines = [
            f"# {obj.name}",
            "",
            f"**Element**: `<{obj.element}>`",
            f"**File**: `{obj.file_path}`",
            "",
            f"**Description**: {obj.description}",
            "",
        ]

        if obj.official_docs:
            lines.append("**Official Documentation**:")
            for doc_url in obj.official_docs:
                lines.append(f"- {doc_url}")
            lines.append("")

        if obj.methods:
            lines.append("**Methods**:")
            for method_name, method_info in list(obj.methods.items())[:5]:  # First 5 methods
                params = method_info.get('params', '')
                desc = method_info.get('description', '').split('.')[0]
                lines.append(f"- {method_name}({params}) - {desc}")
            if len(obj.methods) > 5:
                lines.append(f"... and {len(obj.methods) - 5} more methods")
            lines.append("")

        if obj.attributes:
            lines.append("**Key Attributes**:")
            for attr_name, attr_desc in list(obj.attributes.items())[:5]:  # First 5 attributes
                lines.append(f"- {attr_name}: {attr_desc}")
            if len(obj.attributes) > 5:
                lines.append(f"... and {len(obj.attributes) - 5} more attributes")
            lines.append("")

        lines.append("Use pyrocrail_list_methods to see all methods")
        lines.append(f"See OBJECTS.md#{obj.name.lower()} for complete documentation")

        return '\n'.join(lines)

    def _format_method(self, obj: ObjectInfo, method: str) -> str:
        """Format specific method documentation"""
        if method not in obj.methods:
            return self._method_not_found(obj, method)

        method_info = obj.methods[method]
        params = method_info.get('params', '')
        return_type = method_info.get('return_type', 'None')
        desc = method_info.get('description', '')
        command = method_info.get('command', '')

        lines = [
            f"{obj.name}.{method}({params}) -> {return_type}",
            "",
            desc,
        ]

        if command:
            lines.append(f"\n{command}")

        # Try to extract example from main examples section
        if obj.examples and method in obj.examples:
            lines.append("\nExample:")
            # Find relevant example snippet
            example_lines = []
            in_relevant = False
            for line in obj.examples.split('\n'):
                if f'.{method}(' in line:
                    in_relevant = True
                if in_relevant:
                    example_lines.append(line)
                    if line and not line.startswith(' ') and len(example_lines) > 1:
                        break
            if example_lines:
                lines.append('\n'.join(example_lines[:10]))  # Max 10 lines

        lines.append(f"\nSee: OBJECTS.md#{obj.name.lower()}")

        return '\n'.join(lines)

    def _object_not_found(self, object_type: str) -> str:
        """Format object not found message"""
        all_objects = self.parser.list_all_objects()
        return f"Object type '{object_type}' not found.\n\nAvailable objects:\n" + '\n'.join(f"- {obj}" for obj in all_objects)

    def _method_not_found(self, obj: ObjectInfo, method: str) -> str:
        """Format method not found message"""
        suggestions = self._find_similar_methods(obj, method)
        result = f"Method '{method}' not found for {obj.name}.\n\nAvailable methods:\n"
        result += '\n'.join(f"- {m}()" for m in list(obj.methods.keys())[:10])

        if suggestions:
            result += "\n\nDid you mean:\n"
            result += '\n'.join(f"- {s}()" for s in suggestions[:3])

        return result

    def _find_similar_methods(self, obj: ObjectInfo, method: str) -> list[str]:
        """Find similar method names using simple string matching"""
        if not obj.methods:
            return []

        method_lower = method.lower()
        scored = []

        for existing_method in obj.methods:
            existing_lower = existing_method.lower()
            score = 0

            # Exact substring match
            if method_lower in existing_lower or existing_lower in method_lower:
                score += 10

            # Common prefix
            for i in range(min(len(method_lower), len(existing_lower))):
                if method_lower[i] == existing_lower[i]:
                    score += 1
                else:
                    break

            # Common words
            method_words = set(method_lower.split('_'))
            existing_words = set(existing_lower.split('_'))
            score += len(method_words & existing_words) * 5

            if score > 0:
                scored.append((score, existing_method))

        scored.sort(reverse=True)
        return [method for score, method in scored[:5]]
