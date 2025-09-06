
def binary_search(arr, target):
    """
    Perform binary search on a sorted array.
    
    Args:
        arr: Sorted list of elements
        target: Element to search for
    
    Returns:
        Index of target if found, -1 otherwise
    
    Time Complexity: O(log n)
    Space Complexity: O(1)
    """
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

class TreeNode:
    """Binary tree node implementation"""
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def inorder_traversal(root):
    """
    Perform inorder traversal of binary tree.
    
    Args:
        root: TreeNode representing the root of the tree
    
    Returns:
        List of values in inorder sequence
    """
    result = []
    
    def dfs(node):
        if node:
            dfs(node.left)
            result.append(node.val)
            dfs(node.right)
    
    dfs(root)
    return result
