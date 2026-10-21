# Weekly menu sandbox

This branch is for testing the weekly menu on a laptop. It does not change the Raspberry Pi app or its recipes. The menu starts on Saturday and has blank fields for Saturday through Friday, Snacks, Lunches, and Sweet treats.

## Use the checkout already on this laptop

Open PowerShell in `C:\Users\erica\Desktop\Codex\Recipe Book Weekly Menu Sandbox`, then run:

```powershell
.\run-sandbox.ps1
```

Open <http://127.0.0.1:8783/> and choose **Weekly menu**. Test recipes and menus are saved only in `sandbox_data` inside this checkout. That folder is ignored by Git. Press Ctrl+C to stop the server.

## Clone from GitHub on another laptop

```powershell
git clone --branch sandbox/weekly-menu --single-branch https://github.com/altysmith/Recipe-Book.git "Recipe Book Weekly Menu Sandbox"
cd "Recipe Book Weekly Menu Sandbox"
.\run-sandbox.ps1
```

If you already have this sandbox checkout, use `git pull --ff-only` in that folder to get later updates. The branch is `sandbox/weekly-menu`; `main` and the live app remain separate.
