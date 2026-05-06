## P1966 [NOIP 2013 提高组] 火柴排队

 **提高+/省选−**

**思路**：

求解 $\sum\left(a_i-b_i\right)^2$的最小值。

尝试展开原式：$\sum\left(a_i^2+b_i^2-2\times a_i\times b_i\right)=\sum\left(a_i+b_i\right)^2-2\times\sum\left(a_i\times b_i\right)$。

显然，$\sum\left(a_i+b_i\right)^2$ 是一个定值，原式的大小由 $\sum\left(a_i\times b_i\right)$ 决定，要求最小值，即考虑最大化 $\sum\left(a_i\times b_i\right)$。

根据贪心，我们只需要按照 $a$ 数组的大小关系将 $b$ 数组排序即可。

具体地，令 $p_i$ 表示 $a$ 数组中第 $i$ 小的数对应的下标，$q_i$ 表示 $b$ 数组中第 $i$ 小的数对应的下标。

那么，最后应该需要保证 $\forall i \in[1,n]$ 满足 $p_i=q_i$。那么我们建立辅助映射数组 $t$，令 $t[p_i]=q_i$。

即 $t$ 数组满足 $\forall i\in[i,n]$ 满足 $t_i=i$。即升序排序。因此，具体次数就是求出辅助映射数组的逆序对即可。

可采用归并排序或树状数组求解。时间复杂度：$O(n\log n)$。  

**参考代码**：

```cpp
#include<bits/stdc++.h>

using namespace std;

using i64=long long;

const int mod=1e8-3;
void Showball(){
    int n;
    cin>>n;
    vector<int> a(n+1),b(n+1);

    for(int i=1;i<=n;i++) cin>>a[i];
    for(int i=1;i<=n;i++) cin>>b[i];

    vector<i64> tr(n+1);
    auto add=[&](int x,int v){
        for(;x<=n;x+=x&-x) tr[x]+=v;
    };

    auto ask=[&](int x){
        i64 ret=0;
        for(;x;x-=x&-x) ret+=tr[x];
        return ret;
    };

    vector<int> p(n+1),q(n+1);
    iota(p.begin(),p.end(),0);
    iota(q.begin(),q.end(),0);

    sort(p.begin()+1,p.end(),[&](int x,int y){
        return a[x]<a[y];
    });

    sort(q.begin()+1,q.end(),[&](int x,int y){
        return b[x]<b[y];
    });    

    vector<int> t(n+1);
    for(int i=1;i<=n;i++){
        t[p[i]]=q[i];
    }

    i64 ans=0;
    for(int i=n;i;i--){
        ans=(ans+ask(t[i]-1))%mod;
        add(t[i],1);
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

