#!/bin/bash

set -x
mkdir /tmp/$1
pf="%h %an %ad"
dt="short"
base_filename=$(basename "$2")
echo "Base filename using basename: $base_filename"

# Generation of blame files
#git blame HEAD  $2 > /tmp/$1/$base_filename.head.bl
#git blame HEAD^ $2 > /tmp/$1/$base_filename.head^.bl
#git blame $1  $2 > /tmp/$1/$base_filename.$1.bl
#git blame $1^ $2 > /tmp/$1/$base_filename.$1^.bl

if [[ ! -z "$4" ]]; then
    echo "Line number is specified with git blame"
	IFS=',' read -ra substrings <<< "$4"
	b_output_head=$(git blame --pretty=format:"$pf" --date="$dt" HEAD -L "$4" "$2" )
	b_output_head_p=$(git blame --pretty=format:"$pf" --date="$dt" HEAD^ -L "$4" "$2" )
	b_output_rev=$(git blame --pretty=format:"$pf" --date="$dt" "$1" -L "$4" "$2" )
	b_output_rev_p=$(git blame --pretty=format:"$pf" --date="$dt" "$1^" -L "$4" "$2" )
	echo "$b_output_head" > /tmp/$1/$base_filename.head.bl.${substrings[0]}
	echo "$b_output_head_p" > /tmp/$1/$base_filename.head^.bl.${substrings[0]}
	echo "$b_output_rev" > /tmp/$1/$base_filename.$1.bl.${substrings[0]}
	echo "$b_output_rev_p" > /tmp/$1/$base_filename.$1^.bl.${substrings[0]}
    echo "Generating blame output for function $4"
	exit 0		
fi



# blame_output_head=$(git blame --pretty=format:"$pf" --date="$dt" --line-porcelain HEAD  "$2" )
 if [ -z "$3" ]; then
	blame_output_head=$(git blame --pretty=format:"$pf" --date="$dt" HEAD  "$2" )
	blame_output_head_p=$(git blame --pretty=format:"$pf" --date="$dt" HEAD^  "$2" )
	blame_output_rev=$(git blame --pretty=format:"$pf" --date="$dt" "$1"  "$2" )
	blame_output_rev_p=$(git blame --pretty=format:"$pf" --date="$dt" "$1^"  "$2" )
	echo "$blame_output_head" > /tmp/$1/$base_filename.head.bl
	echo "$blame_output_head_p" > /tmp/$1/$base_filename.head^.bl
	echo "$blame_output_rev" > /tmp/$1/$base_filename.$1.bl
	echo "$blame_output_rev_p" > /tmp/$1/$base_filename.$1^.bl
    echo "No argument provided for function generating for all lines"
  else
	blame_output_head=$(git blame --pretty=format:"$pf" --date="$dt" HEAD -L:"\<$3\>" "$2" )
	blame_output_head_p=$(git blame --pretty=format:"$pf" --date="$dt" HEAD^ -L:"\<$3\>" "$2" )
	blame_output_rev=$(git blame --pretty=format:"$pf" --date="$dt" "$1" -L:"\<$3\>" "$2" )
	blame_output_rev_p=$(git blame --pretty=format:"$pf" --date="$dt" "$1^" -L:"\<$3\>" "$2" )
	echo "$blame_output_head" > /tmp/$1/$base_filename.head.bl.$3
	echo "$blame_output_head_p" > /tmp/$1/$base_filename.head^.bl.$3
	echo "$blame_output_rev" > /tmp/$1/$base_filename.$1.bl.$3
	echo "$blame_output_rev_p" > /tmp/$1/$base_filename.$1^.bl.$3
    	echo "Generating blame output for function $3"
  fi
#blame_output_head=$(git blame --pretty=format:"$pf" --date="$dt" HEAD  "$2" )
#blame_output_head_p=$(git blame --pretty=format:"$pf" --date="$dt" HEAD^  "$2" )
#blame_output_rev=$(git blame --pretty=format:"$pf" --date="$dt" "$1"  "$2" )
#blame_output_rev_p=$(git blame --pretty=format:"$pf" --date="$dt" "$1^"  "$2" )
#blame_output_rev_p=$(git log -5  --pretty=format:"$pf" --date="$dt" "$1^"  "$2"  )

#echo "$blame_output_rev_p"

set +x

