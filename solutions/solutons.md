## [SGU132 Make It Ascending](https://codeforces.com/problemsets/acmsguru/problem/99999/132)

**题目**：

> $M\times N$ 的网格，部分格子有障碍物，其余位空格。求出在空格上放置 $1\times 2$ 或 $2\times 1$ 的骨牌，使得放置后 **不存在两个相邻的空格（即放不下任何骨牌）** 的最小骨牌放置数量。
>
> **骨牌不能重叠，不能覆盖有障碍物的格子**

**数据范围**：$1\le M \le 70,1\le N\le 7$。`*` 表示障碍，`.` 表示空格。

**样例**：

输入：

```cpp
5 5
.*..*
*....
..**.
**.*.
.**..
```

输出

```cpp
4
```



**思路**：

状态压缩 $DP$ + $DFS$ 枚举转移。

观察到每行最多有 $7$ 列，那么我们就可以用二进制数压缩每行的状态，我们在放入 $1\times 2$ 的骨牌时，会影响到下一行，所以转移时需要存储下一行的状态。

容易想到令 $f_{i,j,k}$ 表示当前处理第 $i$ 行且第 $i$ 行状态位 $j$，第 $i+1$ 行状态为 $k$ 的最小骨牌数。

通过 $DFS$ 枚举所有放置状态进行转移即可。一共三种选择:不放，放 $1\times 2$ 的骨牌，放 $2\times 1$ 的骨牌（具体参考代码注释）。

**本题空间限制为 4MB**。所以需要滚动数组优化一下。

**参考代码**：

```CPP
#include<bits/stdc++.h>

using namespace std;

using i64=long long;

const int p[]={1,2,4,8,16,32,64,128};
const int inf=0x3f3f3f3f;

int g[75];//表示原来第i行的状态
int f[2][1<<8][1<<8];
int n,m;
int x=1,st1,st2;
int ans=inf;

//u:当前列号 op1:当前行状态 op2:下一行状态 cnt:已放骨牌数
void dfs(int u,int op1,int op2,int cnt){
    //上一行与当前行都是0,能够放下2x1的，不合法
    if(u>0&&(st1&p[u-1])==0&&(op1&p[u-1])==0) return;
    //当前行的u-1列和u-2列都是0,能够放下1x2的，不合法
    if(u>1&&(op1&p[u-1])==0&&(op1&p[u-2])==0) return;
	
    //处理完所有列
    if(u==m){
        //用上一行的DP值更新该行的DP值
        if(f[x^1][st1][st2]!=inf){
            f[x][op1][op2]=min(f[x][op1][op2],f[x^1][st1][st2]+cnt);
        }
        return;
    }
	
    //该列不放骨牌，状态不变
    dfs(u+1,op1,op2,cnt);
	
    //该列竖着放2x1的骨牌，占用当前行u列与下一行u列
    if((op1&p[u])==0&&(op2&p[u])==0){
        dfs(u+1,op1|p[u],op2|p[u],cnt+1);
    }
	
    //该列横着放1x2的骨牌，占用当前行u列和u+1列
    if(u<m-1&&(op1&p[u])==0&&(op1&p[u+1])==0){
        dfs(u+1,op1|p[u+1]|p[u],op2,cnt+1);
    }
}
void Showball(){
    cin>>n>>m;
    for(int i=1;i<=n;i++){
        string s;
        cin>>s;
        for(auto c:s){
            g[i]=g[i]<<1|(c=='*');//维护每一行的初始状态
        }
    }

    memset(f,0x3f,sizeof f);
	
    //第0行全部不能放，所以状态为2^m-1,第1行状态为g[1]
    f[0][p[m]-1][g[1]]=0;
	
   	//枚举所有合法的上一行状态，再用DFS枚举当前行的放法
    for(int k=1;k<=n;k++){
        for(int i=0;i<p[m];i++){
            for(int j=0;j<p[m];j++){
                if(f[x^1][i][j]!=inf){
                    st1=i,st2=j;
                    dfs(0,j,g[k+1],0);
                }
            }
        }
        memset(f[x^1],0x3f,sizeof f[x^1]);
        x^=1;
    }

    for(int i=0;i<p[m];i++){
        for(int j=0;j<p[m];j++){
     		ans=min(ans,f[x^1][i][j]);
        }
    }

    cout<<ans<<"\n";
}
int main(){
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t=1;
    //cin>>t;

    while(t--){
      Showball();
    }

    return 0;
}
```
