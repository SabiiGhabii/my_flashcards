# Code Formatting and Syntax Highlighting Guide

This guide explains how to use the enhanced code formatting and syntax highlighting features in Plus Ultra Cards for studying programming problems like LeetCode questions.

## Overview

The code formatting system supports:
- **Preserved formatting**: Maintains indentation and newlines in card content
- **Style sections**: Different formatting regions within a single card using markup flags
- **Code syntax highlighting**: Programming language-specific styling with colors and fonts
- **Mixed content**: Both normal text and formatted code sections in the same card
- **Cloze compatibility**: Full integration with cloze deletion functionality

## Markup Syntax

### Basic Code Block
```
{start.style::code[language]}
your code here
{end.style}
```

### Supported Languages
**Priority Languages:**
- `python` - Python
- `cpp` or `c++` - C++
- `rust` - Rust
- `r` - R

**Additional Languages:**
- `javascript` or `js` - JavaScript
- `java` - Java
- `bash` or `shell` - Bash/Shell
- `html` - HTML
- `css` - CSS
- `sql` - SQL
- `c` - C
- `csharp` or `c#` - C#
- `powershell` - PowerShell
- `go` - Go
- `clojure` - Clojure
- `ocaml` - OCaml
- `typescript` or `ts` - TypeScript

### Generic Code Block (no syntax highlighting)
```
{start.style::code}
generic code without language-specific highlighting
{end.style}
```

## Example Usage

### LeetCode Problem Card
```
Merge Sorted Array

This is the problem description in normal text with default styling.

Problem:
{start.style::code[python]}
class Solution(object):
    def merge(self, nums1, m, nums2, n):
        """
        :type nums1: List[int]
        :type m: int
        :type nums2: List[int]
        :type n: int
        :rtype: None Do not return anything, modify nums1 in-place instead.
        """
        a, b, p = m-1, n-1, m+n-1

{{c1::        while b>=0:
            if a>=0 and nums1[a] > nums2[b]:}}
                nums1[p] = nums1[a]
                a -= 1
            else:
{{c2::                nums1[p] = nums2[b]
                b -= 1}}
            p -= 1
{end.style}

Key Points:
- Time Complexity: {{c3::O(m + n)}}
- Space Complexity: {{c4::O(1)}}
```

### Multi-Language Comparison
```
Binary Search Implementation

Python Version:
{start.style::code[python]}
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = {{c1::(left + right) // 2}}
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
{end.style}

C++ Version:
{start.style::code[cpp]}
int binarySearch(vector<int>& arr, int target) {
    int left = 0, right = arr.size() - 1;
    while (left <= right) {
        int mid = {{c2::left + (right - left) / 2}};
        if (arr[mid] == target) return mid;
        else if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}
{end.style}
```

## Card Editor Features

### Enhanced Text Editor
- **Auto-indentation**: Automatically maintains indentation on new lines
- **Smart tab handling**: Converts tabs to 4 spaces for consistent formatting
- **Smart backspace**: Removes 4 spaces at once when in indentation
- **Monospace font**: Uses Courier New for better code readability

### Formatting Toolbar
- **Code Block Menu**: Quick insertion of code blocks for different languages
- **Cloze Buttons**: C1-C5 buttons for quick cloze deletion insertion
- **Live Preview**: Real-time preview with syntax highlighting

### Template System
New code-specific templates:
- **Code Block**: Light theme optimized for code
- **Dark Code**: Dark theme with high contrast for code
- **Retro Terminal**: Green-on-black terminal style

## Study Mode Features

### Enhanced Display
- **Syntax highlighting**: Automatic color coding based on programming language
- **Preserved formatting**: Maintains all indentation and spacing
- **Cloze integration**: Cloze deletions work seamlessly with code blocks
- **Mixed content**: Regular text and code can coexist in the same card

### Cloze Behavior
- **Front side**: Shows code with cloze deletions blanked out as `[ ... ]`
- **Back side**: Shows complete code with syntax highlighting
- **Nested support**: Cloze deletions work inside code blocks

## Technical Implementation

### Core Components
1. **TextFormatter**: Parses markup and handles whitespace preservation
2. **SyntaxHighlighter**: Provides language-specific syntax highlighting
3. **CodeEditorWidget**: Enhanced text editor with code-aware features
4. **FormattedTextDisplay**: Display widget with formatting support

### Fallback Support
- **Without Pygments**: Basic regex-based syntax highlighting
- **Unknown languages**: Falls back to plain code formatting
- **Legacy cards**: Existing cards continue to work unchanged

## Best Practices

### Creating Code Cards
1. Use descriptive problem titles
2. Include problem description in plain text
3. Wrap code in appropriate language blocks
4. Use cloze deletions for key concepts, not syntax
5. Add complexity analysis and key insights

### Cloze Placement
- Focus on algorithmic concepts, not syntax details
- Hide key variable assignments or loop conditions
- Conceal important function calls or operations
- Cover complexity analysis and optimization insights

### Language Selection
- Always specify the language for proper highlighting
- Use standard language identifiers (python, cpp, javascript)
- For pseudocode, use generic code blocks without language

## Troubleshooting

### Common Issues
1. **No syntax highlighting**: Check language spelling and supported languages list
2. **Formatting lost**: Ensure proper markup syntax with matching start/end tags
3. **Cloze not working**: Verify cloze syntax `{{c1::text}}` is correct
4. **Preview not updating**: Check that content change signals are connected

### Performance
- Large code blocks may take longer to highlight
- Complex nested structures should be tested in preview
- Very long cards may need scrolling in study mode

## Migration from Existing Cards

Existing cards will continue to work without modification. To add code formatting:
1. Edit the card in the card editor
2. Wrap code sections with `{start.style::code[language]}` and `{end.style}`
3. Enable "Render as Rich Text" if using templates
4. Preview changes before saving

This system maintains full backward compatibility while providing powerful new formatting capabilities for programming study materials.
