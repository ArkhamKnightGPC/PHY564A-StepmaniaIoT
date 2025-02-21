typedef struct node{
    node *nextNode;
    node *prevNode;
    int reactionTime;

    node(int reactionTime){
        this->nextNode = nullptr;
        this->prevNode = nullptr;
        this->reactionTime = reactionTime;
    }

}node;
typedef node* pnode;

typedef struct fifo{
    pnode firstNode; //to pop first element in O(1)
    pnode lastNode; //to insert new elements in O(1)
    int fifoSize;

    fifo(){
        this->fifoSize = 0;
        this->firstNode = nullptr;
        this->lastNode = nullptr;
    }

    int pop(){//pop first element
        if(this->fifoSize == 0){
            return -1;
        }else{
			pnode toPop = this->firstNode;
			this->firstNode = this->firstNode->nextNode; //move first node reference up
			if(this->firstNode){
				this->firstNode->prevNode = nullptr; //erase reference to node we will pop!
			}
			int ret = toPop->reactionTime;
			delete toPop; //free popped node memory
			this->fifoSize -= 1;
			return ret;
        }
    }

    void add(int reactionTime){//insert new element
        if(this->fifoSize == 0){
            pnode newNode = new node(reactionTime);
			this->firstNode = newNode;
			this->lastNode = newNode;
        }else{
			pnode newNode = new node(reactionTime);
			this->lastNode->nextNode = newNode; //link new node to previous last node
			newNode->prevNode = this->lastNode;
			this->lastNode = newNode;
        }
		this->fifoSize += 1;
		return;
    }

}fifo;
