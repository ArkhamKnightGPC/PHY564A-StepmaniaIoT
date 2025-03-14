#ifndef MINHEAP_HPP
#define MINHEAP_HPP

#include <vector>
#include <algorithm>

// Define the structure for the MinHeap
typedef struct minHeap {
    std::vector<float> heap;  // Vector to store heap elements

    // Helper function to maintain the heap property after insertion
    void heapifyUp(int index) {
        while (index > 0) {
            int parent = (index - 1) / 2;
            if (heap[parent] <= heap[index]) break;
            std::swap(heap[parent], heap[index]);
            index = parent;
        }
    }

    // Helper function to maintain the heap property after extraction
    void heapifyDown(int index) {
        int leftChild, rightChild, smallest;

        while (2 * index + 1 < heap.size()) {
            leftChild = 2 * index + 1;
            rightChild = 2 * index + 2;
            smallest = index;

            if (leftChild < heap.size() && heap[leftChild] < heap[smallest]) {
                smallest = leftChild;
            }
            if (rightChild < heap.size() && heap[rightChild] < heap[smallest]) {
                smallest = rightChild;
            }

            if (smallest == index) break;

            std::swap(heap[index], heap[smallest]);
            index = smallest;
        }
    }

    // Constructor
    minHeap() {}

    // Function to insert a new element into the heap, avoiding duplicates
    void insert(float value) {
        // Check for duplicates
        if (std::find(heap.begin(), heap.end(), value) != heap.end()) {
            return; // Value is already in the heap, so we don't insert it
        }

        // Add the new value to the heap (at the end)
        heap.push_back(value);
        int index = heap.size() - 1;
        heapifyUp(index);  // Restore heap property by moving the value up
    }

    // Function to extract the minimum element (root) from the heap
    float extractMin() {
        if (heap.empty()) {
            return -1;
        }

        // The minimum element is at the root
        float minValue = heap[0];

        // Replace the root with the last element
        heap[0] = heap.back();
        heap.pop_back();

        // Restore the heap property by moving the new root down
        heapifyDown(0);

        return minValue;
    }

    // Function to get the minimum element without extracting it
    float getMin() const {
        if (heap.empty()) {
            return -1;  // or throw an exception
        }
        return heap[0];
    }

    // Function to print the heap
    void printHeap() const {
        for (float value : heap) {
            Serial.print(value);
            Serial.print(" ");
        }
        Serial.println();
    }

    // Function to check if the heap is empty
    bool isEmpty() const {
        return heap.empty();
    }

    // Function to get the size of the heap
    size_t size() const {
        return heap.size();
    }

} minHeap;

#endif // MINHEAP_HPP
