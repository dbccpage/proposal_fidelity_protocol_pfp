# Lesson Sitting Discipline

AuthorityEffect: None.

## The Principle

> One lesson folder teaches one idea. The reader meets that idea in prose, runs it once in the notebook, and can later watch a short clip of the same idea. A second independent idea is a second folder.

## Authoring and Splitting Sittings

1. **Naming**: Name the folder after the notebook stem: `<stem>/<stem>.md`, `<stem>/<stem>.ipynb`, and `<stem>/videos/`.
2. **Prose Opening**: Open the prose page with the idea in sentences a reader can finish in one sitting. Link the companion notebook. State that each clip in `videos/` teaches one step of this same idea and adds no further claim.
3. **Finite Example Scope**: Keep the notebook to one finite example. Later cells may use names defined above them. Do not split a notebook in the middle of a calculation that the next cell still needs.
4. **Media Directory Integrity**: Leave `videos/` empty until a clip exists. One idea per clip. The clip restates the page and the notebook. An empty `videos/` folder containing only `.gitkeep` must never be marketed as complete video instruction.
5. **Segmentation of Long Chapters**: If the page has several independent sections, split them into separate lesson folders, each with its own notebook and `videos/`.
6. **Atomic Notebook-Prose Synchronization**: When the notebook's teaching text changes, regenerate `<stem>.md` in the same edit. The page is a copy; it does not update itself.

## Age Floors

- `000_beginners` states ages 5 to 500.
- The how-to-play manual states ages 11 to 500.
Keep those sentences on their own pages. Do not merge those floors.
