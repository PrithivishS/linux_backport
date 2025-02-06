# backport_tools
Various tools used for backporting projects developed by our team
The main tools are backport.py and patch_info.py.

The new entrant is rvw_diff.py. To use it:
    - add the path to the script to your PATH
    - clone https://github.com/AMDEPYC/Linux_Backport.git
    - check out the appropriate branch
    - rvw_diff.py
      - at the prompt, enter the backported sha id from the code rvw request
      - ^C when you are done

Important things to remember about reviewing backported patches:
	  + you don't need to worry about the main content of an ALREADY UPSTREAMED patch.
	  + you do need to worry about non context diffs where some non context part of
	    upstream patch is modified.
	    - look at the patch description and see that any deviation from the upstream
	      patch is
	      - correct
	      - adequately explained in the [Backport Changes] section of the commit
	        message.

      
You have just read all the documentation available.
For now try the commands with --help and use the source

# Rebase tools
Provides support to export github comments from pre-interactive rebase stage to post 
interactive rebase

# About 
Besides backport tools, this directory also contains git hooks for pre-rebase and post-
rewrite operations

pre-rebase hook is useful during the initialization of git interactive rebase.

While post-rewrite hook is useful after completion of rebase. For carrying out 
operations like git commit --amend, git cherry-pick, etc..,

For this project, post-rewrite hook is designed to only work for 'rebase'.

## Steps
1. Add personal Github token via GITHUB_TOKEN env variable.
	export GITHUB_TOKEN=your_github_token

   You may want to add the above line to ~/.bashrc / ~/.zshrc / ~/.profile to make changes
   persistent.

2. Next, move the files pre-rebase and post-rewrite hooks to $(pwd)/.git/hooks dir.

3. Make these hooks executable:
	chmod +x pre-rebase
	chmod +x post-rewrite

4. Select the number of commits you want to reabse as follows:
	git rebase -i HEAD~15 # 15 commits 

5. Select actions for these commits (pick/reword/rewrite)

6. While these actions take place, pre-rebase hook makes necessary updates to /tmp/comments.json

7. Once after rebase completes, post-rewrite hook gets trigerred that performs git push to the
   upstream branch and thereafter all the github comments are populated from old SHAs to new
   SHAs.

NOTE: Some commits in the rebase may not have comments before the rebase. The post-rewrite hook
honors this absence and leaves the corresponding new SHAs without any comments.

# How to enable

These hooks are disabled by default. 

In order to enable these hooks, move rebase_hook_config.json
to $(pwd)/.git/ directory. 

Then make the following change:
	"hooks_enabled": true

Once after rebase finishes, all the review comments associated with old SHAs are now exported
to new SHAs. This will help reviewers to quickly look at their earlier review comments and ensure
those comments are addressed in the current revision.

For any questions/observations, please reach out to Pavan Kumar Paluri <pavankumar.paluri@amd.com>
 
