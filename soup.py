from xml.dom import Node as NodeType

from bs4 import BeautifulSoup
from bs4.element import Doctype


EXAMPLE_HTML = """\
<!DOCTYPE html>
<html>
<head>
<title>Page Title</title>
</head>
<body>

<h1>This is a Heading</h1>
<p>This is a paragraph.</p>

</body>
</html>
"""

class Node:
    def __init__(self, parent_id, name=None):
        self.parent_id = parent_id
        self.name = name

    def __str__(self):
        return f"Node(parent={self.parent_id}, name={self.name}"


class DocumentNode(Node):
    BS4_TYPE = BeautifulSoup

    def __init__(self, src, parent_id):
        super().__init__(parent_id)
        assert self.parent_id == -1


class DocumentTypeNode(Node):
    BS4_TYPE = Doctype

    def __init__(self, src, parent_id):
        super().__init__(parent_id, name=str(src))


class TreeBuilder:
    NODE_CLASSES = (
        DocumentNode,
        DocumentTypeNode,
    )

    def __init__(self):
        self.nodes = []

    def visit(self, node, parent_id=-1):
        for node_class in self.NODE_CLASSES:
            if isinstance(node, node_class.BS4_TYPE):
                break
        else:
            raise NotImplementedError(type(node))

        node_id = len(self.nodes)
        self.nodes.append(node_class(node, parent_id))
        print(self.nodes[-1])
        for child in getattr(node, "children", ()):
            self.visit(child, node_id)


def main(html=EXAMPLE_HTML):
    tree = TreeBuilder()
    tree.visit(BeautifulSoup(html, "html.parser"))


if __name__ == "__main__":
    main()
