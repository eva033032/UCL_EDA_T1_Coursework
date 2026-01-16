import sys
import os
from subprocess import Popen, PIPE
from Bio import SeqIO
import shutil

"""
usage: python pipeline_script.py INPUT.fasta  
approx 5min per analysis
"""

# ==========================================
# ★★★ 路徑設定 (對應 Ansible 的安裝位置) ★★★
# ==========================================
# S4Pred 的執行檔位置
S4PRED_SCRIPT = '/opt/tools/s4pred/run_model.py'

# HHSearch 的執行檔位置 (等一下我們會用 Ansible 編譯出這個檔案)
HHSEARCH_BIN = '/opt/tools/hh-suite/build/bin/hhsearch'

# PDB70 資料庫的位置 (這是 28GB 資料解壓後的位置)
HHDB_PATH = '/data/pdb70/pdb70'
# ==========================================

def run_parser(hhr_file):
    """
    Run the results_parser.py over the hhr file to produce the output summary
    """
    # 假設 parser 跟這個 script 在同一層目錄
    cmd = ['python3', './results_parser.py', hhr_file]
    print(f'STEP 4: RUNNING PARSER: {" ".join(cmd)}')
    p = Popen(cmd, stdin=PIPE,stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    print(out.decode("utf-8"))
    if err:
        print(f"Parser Error: {err.decode('utf-8')}")

def run_hhsearch(a3m_file):
    """
    Run HHSearch to produce the hhr file
    """
    # 使用修正後的變數路徑
    cmd = [HHSEARCH_BIN,
           '-i', a3m_file, '-cpu', '1', '-d', 
           HHDB_PATH]
    print(f'STEP 3: RUNNING HHSEARCH: {" ".join(cmd)}')
    p = Popen(cmd, stdin=PIPE,stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        print(f"HHSearch Failed: {err.decode('utf-8')}")

def read_horiz(tmp_file, horiz_file, a3m_file):
    """
    Parse horiz file and concatenate the information to a new tmp a3m file
    """
    pred = ''
    conf = ''
    print("STEP 2: REWRITING INPUT FILE TO A3M")
    try:
        with open(horiz_file) as fh_in:
            for line in fh_in:
                if line.startswith('Conf: '):
                    conf += line[6:].rstrip()
                if line.startswith('Pred: '):
                    pred += line[6:].rstrip()
        with open(tmp_file) as fh_in:
            contents = fh_in.read()
        with open(a3m_file, "w") as fh_out:
            fh_out.write(f">ss_pred\n{pred}\n>ss_conf\n{conf}\n")
            fh_out.write(contents)
    except FileNotFoundError:
        print("Error: Temporary files missing. Step 1 (S4Pred) might have failed.")

def run_s4pred(input_file, out_file):
    """
    Runs the s4pred secondary structure predictor to produce the horiz file
    """
    # 使用修正後的路徑，並確保用 python3
    cmd = ['python3', S4PRED_SCRIPT,
           '-t', 'horiz', '-T', '1', input_file]
    print(f'STEP 1: RUNNING S4PRED: {" ".join(cmd)}')
    p = Popen(cmd, stdin=PIPE,stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    
    # 只有成功才寫入檔案
    if p.returncode == 0:
        with open(out_file, "w") as fh_out:
            fh_out.write(out.decode("utf-8"))
    else:
        print(f"S4Pred Error: {err.decode('utf-8')}")

    
def read_input(file):
    """
    Function reads a fasta formatted file of protein sequences
    """
    print("READING FASTA FILES")
    sequences = {}
    ids = []
    # 使用 Biopython 解析
    for record in SeqIO.parse(file, "fasta"):
        sequences[record.id] = record.seq
        ids.append(record.id)
    return(sequences)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 pipeline_script.py <input_fasta>")
        sys.exit(1)

    sequences = read_input(sys.argv[1])
    tmp_file = "tmp.fas"
    horiz_file = "tmp.horiz"
    a3m_file = "tmp.a3m"
    hhr_file = "tmp.hhr"
    
    for k, v in sequences.items():
        print(f'Now analysing input: {k}')
        with open(tmp_file, "w") as fh_out:
            fh_out.write(f">{k}\n")
            fh_out.write(f"{v}\n")
        
        # 依序執行流程
        run_s4pred(tmp_file, horiz_file)
        read_horiz(tmp_file, horiz_file, a3m_file)
        run_hhsearch(a3m_file)
        run_parser(hhr_file)
        
        # 儲存結果
        if os.path.exists("hhr_parse.out"):
            shutil.move("hhr_parse.out", f'{k}_parse.out')
        else:
            print(f"Warning: Analysis for {k} did not generate output.")