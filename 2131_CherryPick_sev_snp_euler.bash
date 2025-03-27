#!/bin/bash

# Define the list of commit hashes you want to cherry-pick
#ee3e88dfec23 perf/mem: Introduce PERF_MEM_LVLNUM_{EXTN_MEM|IO}
#610c238041fb perf/x86/amd: Add IBS OP_DATA2 DataSrc bit definitions
#fec9cc6175d0 perf: Add mem_hops field in perf_mem_data_src structure
#7fbddf40b881 perf: Add new macros for mem_hops field
#3aac580d5cc3perf: Add sample_flags to indicate the PMU-filled sample data
#7c10dd0a88b1 perf/x86/amd: Support PERF_SAMPLE_DATA_SRC
#cb2bb85f7ed8 perf/x86/amd: Support PERF_SAMPLE_ADDR
#6b2ae4952ef8 perf/x86/amd: Support PERF_SAMPLE_{WEIGHT|WEIGHT_STRUCT}
#5b26af6d2b78 perf/x86/amd: Support PERF_SAMPLE_PHY_ADDR
#cfef80bad4cf perf/uapi: Define PERF_MEM_SNOOPX_PEER in kernel header file
#b7ddd38ccc72 tools headers UAPI: Sync include/uapi/linux/perf_event.h header with the kernel
#160ae99365abea perf amd ibs: Sync arch/x86/include/asm/amd-ibs.h header with the kernel
#4173cc055dc9 perf mem/c2c: Set PERF_SAMPLE_WEIGHT for LOAD_STORE events
#923396f6827d perf mem: Add support for printing PERF_MEM_LVLNUM_{CXL|IO}
#d2f327acc63831	perf tools: Support pmu prefix for mem-load event
#f7b58cbdb3ff	perf mem/c2c: Add load store event mappings for AMD
#2c5f652c4426	perf mem/c2c: Avoid printing empty lines for unsupported events
#c72de11605c5	perf mem: Print "LFB/MAB" for PERF_MEM_LVLNUM_LFB
#d79310700590	perf script: Add missing fields in usage hint
#cb6c18b5a416	perf/mem: Rename PERF_MEM_LVLNUM_EXTN_MEM to PERF_MEM_LVLNUM_CXL
#UNMERGED_COMMIT_IDS = ()
#!/bin/bash

# Function to mimic the behavior of atoi
atoi() {
    local str="$1"
    local result=0
    local sign=1
    local i=0

    # Skip leading whitespace
    while [[ $i -lt ${#str} && ${str:i:1} =~ [[:space:]] ]]; do
        ((i++))
    done

    # Check for sign
    if [[ $i -lt ${#str} ]]; then
        if [[ ${str:i:1} == '-' ]]; then
            sign=-1
            ((i++))
        elif [[ ${str:i:1} == '+' ]]; then
            ((i++))
        fi
    fi

    # Convert characters to integer
    while [[ $i -lt ${#str} && ${str:i:1} =~ [0-9] ]]; do
        digit=${str:i:1}
        result=$((result * 10 + digit))
        ((i++))
    done

    # Apply sign
    result=$((result * sign))

    echo "$result"
}


UNMERGED_COMMITS_FILE="unmerged_commits.txt" 
echo "--------LAST RUN------- " >> "$UNMERGED_COMMITS_FILE"

echo " Enter the commit id in current source tree on top of which you want to cherry pick commits list "
read TREE_HEAD

# Check if string is only made up of digits 
#if [[ $TREE_HEAD =~ ^[0-9]+$ ]]; then
#check if string is only made up of hexadigit symbols
#The =~ operator in the if condition is used to perform regular expression matching in shell scripts (specifically in bash).

#integer_value=$(atoi "$TREE_HEAD")

# Check if the input is a valid hexadecimal number
#if [[ $TREE_HEAD =~ ^[0-9a-fA-F]+$ ]]; then
     # Convert the input (decimal number) to hexadecimal
#   hexTREE_HEAD=$(printf "%x\n" "$TREE_HEAD") 
#fi
# Above if condition does not atoi. THerefore implementing a fucntion for atoi

#hexTREE_HEAD=$(atoi "$TREE_HEAD")

if [ ! -z "$TREE_HEAD"  ]; then 
   git reset --hard $TREE_HEAD
fi


#SEV_SNP_EULER_PHASE1_HOST_AND_GUEST=(
#     e97b39c5c436      #gmem
#     c0db19232c1e      #gmem
#     8569992d64b8      #gmem
#     d497a0fab8b8      #gmem
#     1853d7502a19      #gmem
#     4a2e993faad3      #gmem
#     f128cf8cfbec      #gmem
#     16f95f3b95ca      #gmem
#     cec29eef0a81      #gmem
#     193bbfaacc84      #gmem
#     5a475554db1e      #gmem
#     0003e2a41468      #gmem
#     4f0b9194bc11      #gmem
#     a7800aa80ea4      #gmem
#     ee605e315633      #gmem
#     90b4fe17981e      #gmem
#     8dd2eee9d526      #gmem
#     2333afa17af0      #gmem
#     eed52e434bc3      #gmem
#     89ea60c2c7b5      #gmem
#     335869c3f2b8      #gmem
#     8d99e347c097      #gmem
#     bb2968ad6c33      #gmem
#     f7fa67495d11      #gmem
#     01244fce2fa2      #gmem
#     672eaa351015      #gmem
#     242331dfc495      #gmem
#     43f623f350ce      #gmem
#     e6f4f345b259      #gmem
#     2feabb855df8      #gmem
#     8a89efd43423      #gmem
#     e3577788de64      #gmem
#     5d74316466f4      #gmem
#     e3ef461af35a      #guest
#     b6e0f6666f74      #snp_init
#     acaa4b5c4c85      #snp_init
#     04d65a9dbb33      #snp_init
#     216d106c7ff7      #snp_init
#     e3fd08afb7c3      #snp_init
#     94b36bc244bb      #snp_init
#     1f568d36361b      #snp_init
#     54055344b232      #snp_init
#     e8bbd303d7de      #snp_init
#     2c35819ee00b      #snp_init
#     661b1c6169e2      #snp_init
#     3a45dc2b419e      #snp_init
#     1ca5614b84ee      #snp_init
#     18085ac2f2fb      #snp_init
#     8dac642999b1      #snp_init
#     24512afa4336      #snp_init
#     7364a6fbca45      #snp_init
#     a867ad6b340f      #snp_init
#     f366a8dac1b8      #snp_init
#     8ef979584ea8      #snp_init
#     75253db41a46      #snp_init
#     c3b86e61b756      #snp_init
#     f5db8841ebe5      #snp_init
#     fad133c79afa      #snp_init
#     cb645fe478ea      #snp_init
#     d7b69b590bc9      #guest
#)

#      SEV_SNP_EULER_PHASE1_OVMF=(
#      8b66f9df1bb0 #ovmf       
#      f008890ae559 #ovmf       
#      447798cd3a78 #ovmf       
#      3c5f9ac5c3b9 #ovmf       
#      e8c23d1e27f7 #ovmf       
#      97c3f5b8d272 #ovmf       
#      cd6f21522377 #ovmf       
#
#      #--deps for fd290ab86284
#      fded08e744 #fd290ab86284 dependency       
#      52e44713d2 #fd290ab86284 dependency       
#      4329b5b0cd #fd290ab86284 dependency       
#      b7a97bfac5 #fd290ab86284 dependency       
#      e3bd782373 #fd290ab86284 dependency       
#      49b7faba1d #fd290ab86284 dependency       
#      318b0d714a #fd290ab86284 dependency       
#      275d0a39c4 #fd290ab86284 dependency       
#      fd290ab86284 #ovmf
#      
#      f0ed194236b1 #ovmf
#      fecf55a66a1c #ovmf
#      )
SEV_SNP_EULER_PHASE2_HOST_AND_GUEST=(
#e70316d17f6a # Guest patches
#1e52550729da # Guest patches
#88ed43d32beb # Guest patches
#e2f4c8c319ab # Guest patches
#f3c80061c0d3 # snp_init2
#19cebbab995b # snp_init2
#c20722c412f1 # snp_init2
#54f5f47b6055 # snp_init2
#bc6f707fc0fe # snp_init2
#0ecaefb303de # snp_init2
#1ff3c89032a8   # Dependency of 0d7bf5e5b00a
#e7ad84db4d718e   # Dependency of 0d7bf5e5b00a
#b2e02f82b7f762   # Dependency of 0d7bf5e5b00a
#f97314626734de   # Dependency of 0d7bf5e5b00a
#87562052c965ba   # Dependency of 0d7bf5e5b00a
#b4f69df0f65e97   # Dependency of 0d7bf5e5b00a
#0d7bf5e5b00a # snp_init2
#8d2aec3b2d79 # snp_init2
#546d714b0880 # snp_init2
#ac5c48027bac # snp_init2
#605bbdc12bc8
#e1dda3afe2a9f # Dependency of 517987e3fb19
#517987e3fb19
#a1176ef5c92a # Dependency of 2a955c4db1dd
#2a955c4db1dd
#4ebb105e6c6f
#fdd58834d1320 #Dependency of 26c44aa9e076
#26c44aa9e076
#eb4441864e03
#4f5defae7089
#4dd5ecacb9a4
#dfc083a181ba
#6542a00369284c #Dependency of d18c8648166e
#1b78d474ce4ecb #Dependency of d18c8648166e
#126190379c57b7 #Dependency of d18c8648166e
#35f50c91c43e44 #Dependency of d18c8648166e
#57e19f05775847 #Dependency of d18c8648166e
#cd8eb2913205e5 #Dependency of d18c8648166e
#be1bd4c5394ff7 #Dependency of d18c8648166e
#ae20eef5323cce #Dependency of d18c8648166e
#be250ff437fa26 #Dependency of d18c8648166e
#40e09b3ccfacc6 #Dependency of d18c8648166e
#d18c8648166e
4c180a57b03a
#8c53183dbaa2
#d916f00316b2
#ae0181839823
#8d1a36e42be6
#4af663c2f64a
#c72ceafbd12c
#1d23040caa8b
#70623723778a
#fa30b0dc91c8
#3bb2531e20bf
#17573fd971f9
#1f6c06b17751
#a90764f0e4ed
#f32fb32820b1
#b74d002d3d58
#a8e319833355
#1dfe571c12cf
#136d8bc931c8
#dee5a47cc7a4
#ad27ce155566
#0c76b1d08280
#d46b7b6a5f9e
#9b54e248d264
#c63cf135cc99
#e366f92ea99e
#4f2e7aa1cfdf
#8eb01900b018
#b2104024f40c
#ea262f8a7c36
#6f627b425378
#febff040b1a6
#73137f59246d
#b2ec042347fd
#27bd5fdc24c0
#d92205621561
#b7e4be0a224f
#f99b052256f1
#d81473840ce1
#88caf544c930
#f55f3c3ac69f
#74458e4859d8
#332d2c1d713e
#5932ca411e53
#d0d87226f535
#d04c77d23122
#7fbdda31b0a1
#564429a6bd8d
#78c4293372fe
#b85524314a3d
#6dd761d92f66
#7239ed74677a
#de80252414f3
#e300614f10bd
#4b5f67120a88
#e4ee54479273
#66a644c09fbe
)
# Loop through each commit hash
#for COMMIT in "${COMMITS[@]}"
#for COMMIT in "${COMMITS_AMDGITHUB[@]}"
#for COMMIT in "${SEV_SNP_EULER_PHASE1_HOST_AND_GUEST[@]}"
for COMMIT in "${SEV_SNP_EULER_PHASE2_HOST_AND_GUEST[@]}"

do
    echo "Cherry-picking commit $COMMIT"
    # Attempt to cherry-pick the commit
    git cherry-pick $COMMIT

    # Check if the cherry-pick was successful
    if [ $? -ne 0 ]; then
        echo "Cherry-pick of commit $COMMIT failed. Halting script."
        echo "$COMMIT" >> "$UNMERGED_COMMITS_FILE"
	git status 2>&1 | tee $UNMERGED_COMMITS_FILE
	git cherry-pick --abort
        exit 1
    fi
done

echo "All commits cherry-picked successfully."


